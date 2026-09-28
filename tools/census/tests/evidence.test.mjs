import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { ROOT, OUT, acceptedInventory, sha256 } from '../census.mjs';
import { adaptSuite, classEvidence, discoverSuites, readRegistry } from '../evidence.mjs';
import { measureClosure, meterSummary } from '../meter.mjs';

const read = file => fs.readFileSync(path.join(ROOT, 'tools/census', file), 'utf8');
const controls = JSON.parse(read('fixtures/adapters.json')).controls;
const meterControl = JSON.parse(read('fixtures/meter.json'));

for (const control of controls) test(`adapter: ${control.directory}`, () => {
  const adapted = adaptSuite(control.directory, control.manifests);
  assert.equal(adapted.status, 'recognized', adapted.detail);
  assert.deepEqual(adapted.fixtures.map(f => ({ file: f.file,
    stages: Object.fromEntries(Object.entries(f.stages).map(([s, e]) => [s, e.outcome])) })), control.expected);
});

test('known suite with unknown format is reported without partial evidence', () => {
  const data = structuredClone(controls.find(c => c.directory === 'tests/compiler-checker').manifests);
  data['cases.json'].cases[1].knot.exit = 19;
  const adapted = adaptSuite('tests/compiler-checker', data);
  assert.equal(adapted.status, 'unrecognized-format');
  assert.match(adapted.detail, /Unknown expected outcome 19/);
  assert.deepEqual(adapted.fixtures, []);
});

test('absent, mismatched and unsuccessful frozen call evidence cannot imply success', () => {
  const field = controls.find(c => c.directory === 'tests/compiler-fields-wasm');
  const missing = structuredClone(field.manifests);
  delete missing['expectations.json'];
  assert.equal(adaptSuite(field.directory, missing).status, 'unrecognized-format');
  const mismatch = structuredClone(field.manifests);
  mismatch['expectations.json'].observations[0].call.tag = 0;
  assert.equal(adaptSuite(field.directory, mismatch).status, 'unrecognized-format');
  const literals = controls.find(c => c.directory === 'tests/compiler-literals');
  const failed = structuredClone(literals.manifests);
  failed['expectations.json'].fixtures[0].calls[0].seed.exit = 1;
  assert.equal(adaptSuite(literals.directory, failed).status, 'unrecognized-format');
  failed['expectations.json'].fixtures[0].calls = [];
  assert.equal(adaptSuite(literals.directory, failed).status, 'unrecognized-format');
});

test('contradictory classifications and unjoined observations are not recognized', () => {
  const nest = structuredClone(controls.find(c => c.directory === 'tests/compiler-nest').manifests);
  nest['expectations.json'].fixtures[0].knot.outcome = 'Invalid';
  assert.equal(adaptSuite('tests/compiler-nest', nest).status, 'unrecognized-format');
  const generic = structuredClone(controls.find(c => c.directory === 'tests/compiler-generics').manifests);
  generic['expectations.json'].observations.fixtures[0].case = 'unknown';
  assert.equal(adaptSuite('tests/compiler-generics', generic).status, 'unrecognized-format');
});

function scratch(fn) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'knot-census-evidence-'));
  const write = (name, source) => {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), typeof source === 'string' ? source : JSON.stringify(source));
  };
  try {
    write('scripts/gates/run.py', "raise RuntimeError('do not execute')\nGATES = (Gate('checker', ('python3', 'tests/compiler-checker/check.py')), Gate('other', ('python3', 'research/probe/check.py')), Gate('npm', ('npm', 'run', 'test')))\n");
    write('tests/compiler-checker/check.py', '# registered gate\n');
    write('research/probe/check.py', '# registered non-compiler suite\n');
    return fn(root, write);
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
}

test('discovery reads all registrations, unregistered compiler manifests and both companion files', () => scratch((root, write) => {
  const c = controls.find(c => c.directory === 'tests/compiler-fields-wasm');
  for (const [file, data] of Object.entries(c.manifests)) write(c.directory + '/' + file, data);
  write('research/probe/cases.json', { cases: [] });
  write('tests/compiler-mystery/expectations.json', { unknown: true });
  const found = discoverSuites(root);
  assert.deepEqual(found.registry.gates.map(g => g.name), ['checker', 'other', 'npm']);
  assert.equal(found.suites.find(s => s.directory === c.directory).manifests.length, 2);
  assert.equal(found.fixtures.length, 3);
  assert.deepEqual(found.suites.find(s => s.directory === 'research/probe').gates, ['other']);
  assert.equal(found.suites.find(s => s.directory === 'tests/compiler-checker').status, 'no-fixture-manifest');
  assert.ok(found.reports.some(r => r.directory === 'tests/compiler-mystery' && r.status === 'unrecognized-suite'));
  assert.ok(found.reports.some(r => r.directory === 'research/probe' && r.status === 'unrecognized-suite'));
  assert.deepEqual(found, discoverSuites(root));
}));

test('additional or malformed manifests remain visible, never silently absorbed', () => scratch((root, write) => {
  write('tests/compiler-checker/cases.json', { cases: [] });
  write('tests/compiler-checker/expectations.json', { unknown: true });
  let found = discoverSuites(root);
  assert.ok(found.reports.some(r => r.manifest === 'tests/compiler-checker/expectations.json'));
  write('tests/compiler-checker/cases.json', '{bad JSON');
  found = discoverSuites(root);
  assert.equal(found.suites.find(s => s.directory === 'tests/compiler-checker').status, 'unrecognized-format');
  assert.equal(found.fixtures.length, 0);
}));

test('nonliteral registry is rejected rather than partially scanned or executed', () => scratch((root, write) => {
  write('scripts/gates/run.py', "GATES = (Gate('checker', get_argv()),)\n");
  assert.throws(() => readRegistry(root), /Cannot read gate registry/);
  write('scripts/gates/run.py', "GATES = ()\nGATES += (Gate('late', ('python3', 'late.py')),)\n");
  assert.throws(() => readRegistry(root), /Cannot read gate registry/);
}));

test('legacy all-success format cannot absorb explicit failures or malformed call records', () => {
  const manifest = structuredClone(controls.find(c => c.directory === 'tests/compiler-wasm').manifests);
  manifest['cases.json'].cases[0].knot = { exit: 3 };
  assert.equal(adaptSuite('tests/compiler-wasm', manifest).status, 'unrecognized-format');
  delete manifest['cases.json'].cases[0].knot;
  manifest['cases.json'].cases[0].calls = [null];
  assert.equal(adaptSuite('tests/compiler-wasm', manifest).status, 'unrecognized-format');
});

test('agreement formats never overwrite explicit failed outcomes with success', () => {
  const generic = structuredClone(controls.find(c => c.directory === 'tests/compiler-generics').manifests);
  generic['expectations.json'].cases[0].knot.exit = 3;
  assert.equal(adaptSuite('tests/compiler-generics', generic).status, 'unrecognized-format');
  assert.equal(adaptSuite('tests/compiler-generics', { 'expectations.json': null }).status, 'unrecognized-format');
  const modules = structuredClone(controls.find(c => c.directory === 'tests/compiler-modules').manifests);
  modules['expectations.json'].fixtures[0].knot.exit = 3;
  assert.equal(adaptSuite('tests/compiler-modules', modules).status, 'unrecognized-format');
  const wasm = structuredClone(controls.find(c => c.directory === 'tests/compiler-wasm').manifests);
  wasm['cases.json'].cases[0].calls[0].exit = 4;
  assert.equal(adaptSuite('tests/compiler-wasm', wasm).status, 'unrecognized-format');
});

test('evidence discovery refuses symlink escapes without reading the target', () => scratch((root, write) => {
  write('tests/compiler-checker/cases.json', { cases: [] });
  fs.symlinkSync(path.join(ROOT, 'tools/census/fixtures/adapters.json'), path.join(root, 'tests/compiler-checker/expectations.json'));
  assert.throws(() => discoverSuites(root), /Evidence path escapes repository/);
}));

test('module fixtures resolve bare-relative imports and verify frozen package bytes without cache fallback', () => scratch((root, write) => {
  const directory = 'tests/compiler-modules', hash = '0x1234', bit = read('fixtures/control.bend');
  const source = `import lib/bit.bend as L\nimport ${hash}/bit.bend as P\ndef main() -> L.Bit: L.identity(L.Low{})\n`;
  write(directory + '/fixtures/main.bend', source);
  write(directory + '/fixtures/lib/bit.bend', bit);
  write(`${directory}/bundle/lib/${hash}/bit.bend`, bit);
  const data = { sources: { 'fixtures/main.bend': sha256(source), 'fixtures/lib/bit.bend': sha256(bit) },
    bundle: { packages: { [hash]: { files: { 'bit.bend': sha256(bit) } } } },
    fixtures: [{ file: 'fixtures/main.bend', knot: { obligation: 'match-seed' }, calls: [{ exit: 0, tag: 0 }] }] };
  write(directory + '/expectations.json', data);
  const result = acceptedInventory(root);
  for (const feature of ['imports.local', 'imports.package']) {
    assert.equal(result.classes.find(c => c.feature === feature).stages.check.evidence.length, 1);
  }
  write(`${directory}/bundle/lib/${hash}/bit.bend`, bit + '\n');
  assert.throws(() => acceptedInventory(root), /Fixture package pin differs/);
  write(`${directory}/bundle/lib/${hash}/bit.bend`, bit);
  write(directory + '/fixtures/lib/bit.bend', bit + '\n');
  assert.throws(() => acceptedInventory(root), /Fixture module pin differs/);
  write(directory + '/fixtures/lib/bit.bend', bit);
  write(directory + '/fixtures/main.bend', source + '\n');
  assert.throws(() => acceptedInventory(root), /Frozen fixture hash differs/);
}));

test('negative module analysis is byte-identical after moving the checkout', () => {
  const results = [];
  for (let i = 0; i < 2; i++) scratch((root, write) => {
    const directory = 'tests/compiler-modules';
    const source = 'import ./absent.bend as M\ndef identity(x: M.Bit) -> M.Bit: x\n';
    write(directory + '/fixtures/missing.bend', source);
    write(directory + '/expectations.json', {
      sources: { 'fixtures/missing.bend': sha256(source) },
      fixtures: [{ file: 'fixtures/missing.bend', knot: { obligation: 'reject', outcome: 'Invalid', exit: 2 } }],
    });
    const accepted = acceptedInventory(root), fixture = accepted.fixtures[0];
    assert.equal(fixture.analysis.outcome, 'HostFailure');
    assert.match(fixture.analysis.detail, /\$ROOT\/tests\/compiler-modules/);
    assert.ok(!JSON.stringify(accepted).includes(root));
    results.push(accepted);
  });
  assert.deepEqual(results[0], results[1]);
});

const record = (outcome, features = ['lambdas']) => ({ suite: 'control', file: 'a.bend', features, stages: { check: { outcome } } });
const checkFailed = fn => {
  for (const state of ['Invalid', 'Unsupported', 'Exhausted', 'HostFailure', 'InternalFailure', 'Unfixed']) {
    assert.deepEqual(fn([record(state)], ['lambdas'])[0].stages.check.evidence, []);
  }
};
test('a failure or ambiguous outcome supplies no positive class evidence', () => checkFailed(classEvidence));

test('stage evidence is exact, sorted, deduplicated and never inferred from compilation', () => {
  const r = record('Checked', ['fields']);
  r.stages.compile = { outcome: 'Built' };
  const stages = classEvidence([r, r], ['fields'])[0].stages;
  assert.deepEqual(stages.check.evidence, ['control:a.bend']);
  assert.deepEqual(stages.wasm.evidence, []);
  assert.deepEqual(stages.parse.evidence, []);
  assert.deepEqual(stages.catalog.evidence, []);
  r.stages.check.outcome = 'Built';
  assert.deepEqual(classEvidence([r], ['fields'])[0].stages.check.evidence, []);
});

test('new suites supply recursion check/eval and fields Wasm evidence with exhaustion excluded', () => {
  const accepted = acceptedInventory();
  const recursion = accepted.classes.find(c => c.feature === 'recursion').stages;
  assert.ok(recursion.check.evidence.some(e => e.startsWith('recursion:')));
  assert.ok(recursion.eval.evidence.some(e => e.startsWith('recursion:')));
  assert.deepEqual(recursion.wasm.evidence, []);
  const fields = accepted.classes.find(c => c.feature === 'fields').stages;
  assert.ok(fields.wasm.evidence.some(e => e.startsWith('fields-wasm:')));
  assert.ok(!fields.wasm.evidence.some(e => e.endsWith('/arena-overflow.bend')));
  const exhausted = accepted.fixtures.find(f => f.suite === 'fields-wasm' && f.file.endsWith('/deep-call.bend'));
  assert.equal(exhausted.stages.eval.outcome, 'Exhausted');
  assert.equal(exhausted.stages.wasm.outcome, 'Built');
  assert.equal(accepted.suites.find(s => s.suite === 'fields-wasm').fixtures, 8);
  assert.equal(accepted.suites.find(s => s.suite === 'recursion').fixtures, 19);
});

function literalMeter(fn = measureClosure, control = meterControl) {
  return fn(control.closure, control.files, Object.fromEntries(Object.entries(control.evidence).map(([s, f]) => [s, new Set(f)])));
}
function checkMeter(fn) {
  const result = literalMeter(fn), expected = meterControl.expected;
  for (const key of ['declarations', 'check', 'wasm']) assert.equal(result.totals[key], expected[key], key);
  assert.deepEqual(result.missing, expected.missing);
  assert.deepEqual(Object.fromEntries(result.declarations.map(d => [d.key, d.missing])), expected.per_declaration);
}
test('meter matches literal counts, ranked blockers and each declaration gap', () => checkMeter(measureClosure));

test('imports block declarations; runtime laws/fills in ordinary files merge into one counted identity', () => {
  const control = structuredClone(meterControl);
  control.files[0].imports.push({ feature: 'imports.base' });
  control.files[0].declarations.push({ key: 'src/control.law', kind: 'law', features: ['laws'] },
    { key: 'src/control.law', kind: 'law_fill', features: ['proofs'] });
  control.closure.entries.push({ key: 'src/control.law', file: 'src/control.bend', boundary: 'source' });
  const result = literalMeter(measureClosure, control);
  assert.equal(result.totals.declarations, 4);
  assert.equal(result.totals.check, 0);
  assert.equal(result.totals.wasm, 0);
  assert.deepEqual(result.missing.check[0], { feature: 'imports.base', declarations: 4 });
  assert.equal(result.excluded.length, 1);
  assert.deepEqual(result.declarations.find(d => d.key === 'src/control.law').features, ['imports.base', 'laws', 'proofs']);
});

test('meter fails on unresolved or missing declarations instead of shrinking its denominator', () => {
  const control = structuredClone(meterControl);
  control.closure.unresolved = [{ key: 'unknown' }];
  assert.throws(() => literalMeter(measureClosure, control), /unresolved/);
  control.closure.unresolved = [];
  control.files[0].declarations.pop();
  assert.throws(() => literalMeter(measureClosure, control), /Missing meter declaration/);
  control.closure.entries.push(control.closure.entries[0]);
  assert.throws(() => literalMeter(measureClosure, control), /Duplicate meter declaration/);
});

test('meter summary is deterministic and fits on one screen', () => {
  const result = literalMeter();
  const meter = { roots: { compiler: result, frontend: result }, suite_reports: [] };
  const summary = meterSummary(meter);
  assert.equal(summary, meterSummary(meter));
  assert.match(summary, /check 2\/3; Wasm 1\/3/);
  assert.ok(summary.split('\n').length <= 14);
});

test('meter CLI is read-only and repeats byte-identically', () => {
  const files = [...fs.readdirSync(path.join(ROOT, OUT)).filter(f => f.endsWith('.json')).map(f => path.join(OUT, f)), 'tools/census/approved.json'];
  const hashes = () => files.map(f => sha256(fs.readFileSync(path.join(ROOT, f))));
  const before = hashes();
  const run = () => spawnSync('node', ['tools/census/census.mjs', '--meter'], {
    cwd: ROOT, encoding: 'utf8', env: { ...process.env, BEND_NO_TELEMETRY: '1' }, timeout: 30000,
  });
  const first = run(), second = run();
  assert.equal(first.status, 0, first.stderr);
  assert.equal(second.status, 0, second.stderr);
  assert.equal(first.stdout, second.stdout);
  assert.match(first.stdout, /compiler: \d+ declarations/);
  assert.match(first.stdout, /frontend: \d+ declarations/);
  assert.deepEqual(hashes(), before);
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

test('semantic mutant: counting failed fixtures is killed by the fixed outcome controls', async () => {
  const m = await mutant('evidence.mjs', 'r.stages[stage]?.outcome === success', 'r.stages[stage] !== undefined');
  checkFailed(classEvidence);
  assert.throws(() => checkFailed(m.classEvidence), assert.AssertionError);
});

function checkUnknown(fn) {
  const adapted = fn('tests/compiler-mystery', { 'cases.json': { cases: [
    { file: 'tests/compiler-mystery/a.bend', calls: [{ export: 'main', arguments: [], tag: 1 }] },
  ] } });
  const evidence = classEvidence(adapted.fixtures.map(f => ({ ...f, suite: 'unknown', features: ['lambdas'] })), ['lambdas']);
  assert.deepEqual(evidence[0].stages.check.evidence, []);
}
test('semantic mutant: guessing an unknown suite is killed by the isolated lambda class', async () => {
  const m = await mutant('evidence.mjs', 'const adapter = ADAPTERS[directory];', "const adapter = ADAPTERS[directory] ?? ADAPTERS['tests/compiler-wasm'];");
  checkUnknown(adaptSuite);
  assert.throws(() => checkUnknown(m.adaptSuite), assert.AssertionError);
});

test('semantic mutant: counting a law-file helper is killed by the fixed denominator', async () => {
  const m = await mutant('meter.mjs', 'if (lawFile(entry.file))', 'if (false)');
  checkMeter(measureClosure);
  assert.throws(() => checkMeter(m.measureClosure), assert.AssertionError);
});
