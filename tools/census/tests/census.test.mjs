import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { Inventory, ROOT, OUT, build, closure, intrinsicOperations, wordRepresentations,
  approvedPolicy, policyViolations, packageCatalog, acceptedInventory, outcome, json, sha256 } from '../census.mjs';

const fixture = name => fs.readFileSync(path.join(ROOT, 'tools/census/fixtures', name), 'utf8');
const expected = JSON.parse(fixture('expected.json'));
const comp = fs.readFileSync(path.join(ROOT, '.toolchain/bend-2.0.29-574b6d3/bend2/comp.ts'), 'utf8');
const operations = intrinsicOperations(comp);
function analyze(source, file = 'src/probe.bend', extra = []) {
  const inv = new Inventory({ sources: new Map([[file, source], ...extra]) });
  inv.load(file);
  return { inv, files: inv.manifest() };
}
function declaration(files, name, kind) {
  const d = files.flatMap(f => f.declarations).find(d => d.name === name && (!kind || d.kind === kind));
  assert.ok(d, `${name}:${kind ?? '*'}`); return d;
}

test('literal-reviewed feature expectations', () => {
  const inputs = new Map(['control.bend', 'lambda.bend', 'features.bend'].map(f => [f, analyze(fixture(f), f)]));
  for (const [key, observation] of Object.entries(expected.declarations)) {
    const [file, selector] = key.split('::'), [name, kind] = selector.split(':');
    const d = declaration(inputs.get(file).files, name, kind);
    if (observation.exact) assert.deepEqual(d.features, observation.exact, key);
    for (const f of observation.includes ?? []) assert.ok(d.features.includes(f), `${key} includes ${f}`);
    for (const f of observation.excludes ?? []) assert.ok(!d.features.includes(f), `${key} excludes ${f}`);
    if (observation.capture_names) assert.deepEqual(d.captures.flatMap(c => c.names), observation.capture_names, key);
  }
});

for (const name of ['control.bend', 'lambda.bend', 'features.bend']) {
  test(`pinned seed completely checks ${name}`, () => {
    const r = spawnSync('bun', ['.toolchain/bend-2.0.29-574b6d3/bend2/main.ts', `tools/census/fixtures/${name}`, '--check-only'], {
      cwd: ROOT, encoding: 'utf8', env: { ...process.env, BEND_NO_TELEMETRY: '1' }, timeout: 30000,
    });
    assert.equal(r.status, 0, r.stderr);
    assert.equal(r.stdout.trim(), 'All terms check.');
  });
}

test('a synthetic added lambda violates the original declaration approval', () => {
  const baseline = analyze(fixture('control.bend'));
  const changed = analyze(fixture('lambda.bend'));
  const violations = policyViolations(changed.files, approvedPolicy(baseline.files));
  assert.ok(violations.some(v => v.includes('identity:definition: unapproved feature lambdas')));
});

test('an unused Base import is still an unapproved import', () => {
  const baseline = analyze(fixture('control.bend'));
  const changed = analyze('import Base\n' + fixture('control.bend'));
  assert.ok(policyViolations(changed.files, approvedPolicy(baseline.files)).some(v => v.includes('unapproved import Base')));
});

test('an unused Vec import exposes arrays transitively, even after approving that import', () => {
  const pkgs = packageCatalog(ROOT), vec = pkgs.find(p => p.name === 'vec');
  const file = 'src/probe.bend', inv = new Inventory({ packages: pkgs });
  const original = inv.source.bind(inv);
  inv.source = f => f === file ? `import ${vec.hash}/main.bend as V\n` + fixture('control.bend') : original(f);
  inv.load(file);
  const files = inv.manifest();
  const baseline = analyze(fixture('control.bend'));
  assert.ok(policyViolations(files, approvedPolicy(baseline.files)).some(v => v.includes('unapproved import ' + vec.hash)));
  assert.ok(policyViolations(files, approvedPolicy(files)).some(v => v.includes(`${vec.hash}/main.bend: forbidden dependency feature arrays`)));
});

test('feature-like comments and string contents do not create lambdas or imports', () => {
  const { files } = analyze('# import vec as V; x => Array.new\nimport Base\ndef text() -> String: "x => Array.new"\n');
  const text = declaration(files, 'text');
  assert.ok(!text.features.includes('lambdas'));
  assert.ok(!text.features.includes('arrays'));
  assert.deepEqual(files.find(f => f.file === 'src/probe.bend').imports.map(i => i.module), ['Base']);
});

test('shadowed bindings are excluded from capture sets', () => {
  const { files } = analyze('import Base\ndef f(+x: U32) -> U32 -> U32: x => x\n');
  assert.ok(!declaration(files, 'f').features.includes('captures'));
});

test('array and tuple sugars retain their own literal classes', () => {
  const { files } = analyze('import Base\ndef array() -> Array<U32>: [0 : U32 * 4n]\ndef tuple() -> U32 & U32: (1,2)\n');
  assert.ok(declaration(files, 'array').features.includes('literals.array'));
  assert.ok(declaration(files, 'array').features.includes('arrays'));
  assert.ok(declaration(files, 'tuple').features.includes('literals.tuple'));
});

test('quantity arguments are not fabricated from Type or Data kind sugar', () => {
  assert.ok(!analyze(fixture('control.bend')).files[0].features.includes('quantities.arguments'));
});

test('named function values and partial applications differ from saturated calls', () => {
  const { files } = analyze('import Base\ndef add(x: U32, y: U32) -> U32: U32.add(x,y)\ndef partial(x: U32) -> U32 -> U32: add(x)\ndef value() -> U32 -> U32 -> U32: add\ndef invoke() -> U32: add(1,2)\ndef annotated() -> U32: {add : U32 -> U32 -> U32}(1,2)\n');
  assert.ok(declaration(files, 'partial').features.includes('calls.partial'));
  assert.ok(declaration(files, 'value').features.includes('function-values'));
  assert.ok(!declaration(files, 'invoke').features.includes('calls.partial'));
  assert.ok(!declaration(files, 'invoke').features.includes('function-values'));
  assert.ok(!declaration(files, 'annotated').features.includes('function-values'));
});

test('forward and mutually recursive datatype references resolve without textual guessing', () => {
  const { files } = analyze('type A is Data:\n  A{next: B}\ntype B is Data:\n  End{}\n  B{next: A}\n');
  assert.ok(declaration(files, 'A').references.includes('src/probe.B'));
  assert.ok(declaration(files, 'B').references.includes('src/probe.A'));
});

test('law fills retain separate declaration evidence and the law signature', () => {
  const { files } = analyze(fixture('features.bend'));
  const law = declaration(files, 'same', 'law'), proof = declaration(files, 'same', 'law_fill');
  assert.notEqual(law.id, proof.id);
  assert.equal(law.key, proof.key);
  assert.ok(law.type_references.includes('U32'));
});

test('imports resolve exact offline module identities; aliases do not become declarations', () => {
  const { inv, files } = analyze('import ./dep.bend as D\ndef f(x: D.Bit) -> D.Bit: D.identity(x)\n', 'src/probe.bend', [['src/dep.bend', fixture('control.bend')]]);
  const f = declaration(files, 'f');
  assert.deepEqual(f.execution.references, ['src/dep.identity']);
  const c = closure(['src/probe.f'], files.flatMap(f => f.declarations), inv.book, operations);
  assert.deepEqual(c.entries.map(d => d.key), ['src/dep.identity', 'src/probe.f']);
  assert.deepEqual(c.unresolved, []);
});

test('missing and external imports fail closed without fetching', () => {
  assert.throws(() => analyze('import ./missing.bend as M\n'), e => e.outcome === 'ResolutionFailure');
  assert.throws(() => analyze('import 0x123/main.bend as M\n'), e => e.outcome === 'Unsupported');
  assert.throws(() => analyze('import ../../../outside.bend as M\n'), e => e.outcome === 'ResolutionFailure');
});

test('the source loader rejects a symlink escaping its repository', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'knot-census-'));
  try {
    fs.mkdirSync(path.join(dir, 'root'));
    fs.writeFileSync(path.join(dir, 'outside.bend'), fixture('control.bend'));
    fs.symlinkSync('../outside.bend', path.join(dir, 'root/link.bend'));
    assert.throws(() => new Inventory({ root: path.join(dir, 'root') }).load('link.bend'), e => e.outcome === 'ResolutionFailure');
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('pinned OPERATIONS expands computed names and preserves target differences', () => {
  for (const name of ['u32_add', 'u32_is_eq', 'f32_atan2', 'nat_max', 'array_atomic_cas']) assert.ok(operations[name], name);
  assert.deepEqual(operations.string_append, { js: true, native: false });
  assert.deepEqual(wordRepresentations(comp), ['F32', 'Nat', 'U32']);
  assert.throws(() => intrinsicOperations(comp + '\n'), /pin changed/);
});

function arithmeticClosure(closureFn = closure) {
  const { inv, files } = analyze('import Base\ndef main() -> U32: U32.add(1,2)\n');
  return closureFn(['src/probe.main'], files.flatMap(f => f.declarations), inv.book, operations);
}
test('the intrinsic cut retains the operation and stops before its source implementation', () => {
  const c = arithmeticClosure();
  assert.deepEqual(c.entries.map(d => [d.key, d.boundary]), [['src/probe.main', 'source'], ['U32.add', 'intrinsic']]);
  assert.deepEqual(c.entries.find(d => d.key === 'U32.add').dependencies, []);
});

test('a local lookalike of an intrinsic does not acquire Base privilege', () => {
  const { inv, files } = analyze('type Bit is Data:\n  Low{}\ndef U32.add(x: Bit, y: Bit) -> Bit: x\ndef main() -> Bit: U32.add(Low{},Low{})\n');
  const c = closure(['src/probe.main'], files.flatMap(f => f.declarations), inv.book, operations);
  assert.equal(c.entries.find(d => d.key === 'src/probe.U32.add').boundary, 'source');
});

test('loading Base after another module never marks that module as trusted Base', () => {
  const inv = new Inventory({ sources: new Map([['src/local.bend', fixture('control.bend')]]) });
  inv.load('src/local.bend'); inv.load('Base');
  assert.equal(inv.book.tlds['src/local.identity'].b, undefined);
  assert.equal(inv.book.tlds['U32.add'].b, true);
});

test('GPU offload syntax is a forbidden dependency feature', () => {
  const { files } = analyze('import Base\ndef add(x: U32) -> U32: U32.add(x,1)\ndef main() -> U32: add!(1)\n');
  assert.ok(declaration(files, 'main').features.includes('calls.offload'));
  assert.ok(policyViolations(files, approvedPolicy(files)).some(v => v.includes('forbidden dependency feature calls.offload')));
});

test('erased arguments and annotations remain static evidence but do not add execution calls', () => {
  const source = 'import Base\ndef ghost() -> U32: U32.mul(3,4)\ndef take(-x: U32, y: U32) -> U32: y\ndef main() -> U32: take(ghost(),1)\n';
  const { inv, files } = analyze(source), ds = files.flatMap(f => f.declarations);
  const runtime = closure(['src/probe.main'], ds, inv.book, operations);
  assert.ok(!runtime.entries.some(d => d.key === 'src/probe.ghost'));
  const statics = closure(['src/probe.main'], ds, inv.book, operations, 'static');
  assert.ok(statics.entries.some(d => d.key === 'src/probe.ghost'));
});

test('closed template value arguments remain execution dependencies despite erasure', () => {
  const source = 'import Base\ndef add(x: U32) -> U32: U32.add(x,1)\ndef template(~f: U32 -> U32, x: U32) -> U32: f(x)\ndef main() -> U32: template(~add,1)\n';
  const { inv, files } = analyze(source), ds = files.flatMap(f => f.declarations);
  const c = closure(['src/probe.main'], ds, inv.book, operations);
  assert.ok(c.entries.some(d => d.key === 'src/probe.add'));
  assert.ok(c.entries.some(d => d.key === 'U32.add' && d.boundary === 'intrinsic'));
  assert.deepEqual(c.entries.find(d => d.key === 'src/probe.template').dynamic_calls, ['f']);
});

test('large Nat literals retain the seed implicit U32.to_nat dependency', () => {
  const { inv, files } = analyze('import Base\ndef main() -> Nat: 257n\n');
  const c = closure(['src/probe.main'], files.flatMap(f => f.declarations), inv.book, operations);
  assert.deepEqual(c.entries.map(d => d.key), ['src/probe.main', 'U32.to_nat']);
  assert.equal(c.entries[1].boundary, 'intrinsic');
});

test('outcomes stay separate; a timeout or host failure never becomes Invalid', () => {
  assert.deepEqual([0, 2, 3, 4, 5, 6].map(exit => outcome({ exit }, 'Checked')),
    ['Checked', 'Invalid', 'Unsupported', 'Exhausted', 'HostFailure', 'InternalFailure']);
  assert.throws(() => outcome({ exit: null }, 'Checked'), /Unknown expected outcome/);
});

test('accepted evidence distinguishes field evaluation, declaration inspection and fielded Wasm', () => {
  const accepted = acceptedInventory();
  const fields = accepted.classes.find(c => c.feature === 'fields').stages;
  assert.equal(fields.catalog.status, 'observed-in-successful-fixtures');
  assert.equal(fields.check.status, 'observed-in-successful-fixtures');
  assert.equal(fields.eval.status, 'observed-in-successful-fixtures');
  assert.equal(fields.wasm.status, 'observed-in-successful-fixtures');
  const lambdas = accepted.classes.find(c => c.feature === 'lambdas').stages;
  assert.equal(lambdas.wasm.status, 'no-positive-fixture-evidence');
  assert.ok(accepted.fixtures.some(f => Object.values(f.stages).some(s => s.outcome === 'Unsupported')));
  assert.ok(accepted.fixtures.some(f => Object.values(f.stages).some(s => s.outcome === 'Invalid')));
  assert.equal(accepted.suites.find(s => s.suite === 'wasm').fixtures, 25);
});

test('regeneration is byte-identical and matches every committed manifest', () => {
  const first = build(), second = build();
  for (const file of Object.keys(first)) {
    assert.equal(json(first[file]), json(second[file]), file);
    assert.equal(fs.readFileSync(path.join(ROOT, OUT, file), 'utf8'), json(first[file]), file);
  }
  assert.equal(first['implementation.json'].totals.frontend_files.definitions, expected.execution.frontend_definitions);
  const front = first['base-closure.json'].roots.frontend;
  assert.equal(front.js.totals.base, expected.execution.base_runtime_entries);
  assert.equal(front.js.totals.base_intrinsics, expected.execution.js_intrinsics);
  assert.equal(front.native.totals.base_intrinsics, expected.execution.native_intrinsics);
  assert.equal(front.js.totals.foreign, expected.execution.foreign);
  const hosts = first['hosts.json'];
  assert.equal(hosts.base_trust.entries, 466);
  assert.equal(hosts.base_trust.foreign.length, 42);
  assert.deepEqual(hosts.base_trust.unsafe, ['Array.fork', 'Array.join']);
  assert.deepEqual(hosts.artifacts.compiler.js.foreign,
    ['File.close', 'File.open', 'File.read', 'File.write_bytes', 'IO.args', 'IO.print', 'src/path-host.inspect']);
  assert.deepEqual(hosts.artifacts.frontend.js.foreign, []);
});

test('CLI --check succeeds without changing inventory or approval bytes', () => {
  const files = [...fs.readdirSync(path.join(ROOT, OUT)).filter(f => f.endsWith('.json')).map(f => path.join(OUT, f)), 'tools/census/approved.json'];
  const before = files.map(f => sha256(fs.readFileSync(path.join(ROOT, f))));
  const r = spawnSync('node', ['tools/census/census.mjs', '--check'], { cwd: ROOT, encoding: 'utf8', env: { ...process.env, BEND_NO_TELEMETRY: '1' }, timeout: 30000 });
  assert.equal(r.status, 0, r.stderr);
  assert.deepEqual(files.map(f => sha256(fs.readFileSync(path.join(ROOT, f)))), before);
});

async function mutant(file, before, after) {
  const target = path.join(ROOT, 'tools/census', file);
  let source = fs.readFileSync(target, 'utf8');
  assert.equal(source.split(before).length - 1, 1, 'unique mutant anchor');
  source = source.replace(before, after).replaceAll('import.meta.url', JSON.stringify(pathToFileURL(target).href));
  source = source.replace(/from '([^']+)'/g, (match, module) => module.startsWith('.')
    ? `from '${pathToFileURL(path.resolve(path.dirname(target), module)).href}'` : match);
  const checked = spawnSync('node', ['--check', '--input-type=module'], { input: source, encoding: 'utf8' });
  assert.equal(checked.status, 0, checked.stderr);
  return import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
}

test('semantic mutant: dropping lambda detection is killed by the frozen lambda witness', async () => {
  const m = await mutant('features.mjs', "add('lambdas');", 'void 0;');
  const { inv } = analyze(fixture('lambda.bend'));
  const d = inv.declarations.find(d => d.name === 'identity');
  assert.throws(() => assert.ok(m.classify(d, inv.book).features.includes('lambdas')), assert.AssertionError);
});

test('semantic mutant: ignoring import approval is killed by an unused import', async () => {
  const m = await mutant('census.mjs', 'if (!approved?.imports.some(', 'if (false && !approved?.imports.some(');
  const baseline = analyze(fixture('control.bend')), changed = analyze('import Base\n' + fixture('control.bend'));
  const check = fn => assert.ok(fn(changed.files, approvedPolicy(baseline.files)).some(v => v.includes('unapproved import Base')));
  check(policyViolations);
  assert.throws(() => check(m.policyViolations), assert.AssertionError);
});

test('semantic mutant: bypassing the intrinsic cut is killed by dependency observations', async () => {
  const m = await mutant('census.mjs', '(intrinsic || foreign || representation)', '(foreign || representation)');
  const check = c => assert.deepEqual(c.entries.find(d => d.key === 'U32.add').dependencies, []);
  check(arithmeticClosure());
  assert.throws(() => check(arithmeticClosure(m.closure)), assert.AssertionError);
});

test('semantic mutant: conflating Unsupported with Invalid is killed by classification', async () => {
  const m = await mutant('evidence.mjs', "3: 'Unsupported'", "3: 'Invalid'");
  assert.equal(outcome({ exit: 3 }, 'Built'), 'Unsupported');
  assert.throws(() => assert.equal(m.outcome({ exit: 3 }, 'Built'), 'Unsupported'), assert.AssertionError);
});
