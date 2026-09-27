import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { install, patchPerch } from '../scripts/install-perch-bend.mjs';
import { runPerch } from '../scripts/perch-workflow.mjs';
import { analyzeBendSource } from '../scripts/perch-bend.mjs';
import { createBendReview, createBendSourceSnapshot } from '../scripts/perch-bend-context.mjs';
import { prepareStyleTargets, prepareStyleComposition } from '../scripts/perch-style.mjs';

test('pinned installation is repeatable and refuses unknown bundle contents', async () => {
  const first = await install();
  const second = await install();
  assert.deepEqual(first, second);
  assert.throws(() => patchPerch('wrong bundle', 'test'), /anchor changed/);
});

test('file checks run real method rules per working-copy declaration with relevant helper and law context', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-bend-units-'));
  const realFetch = globalThis.fetch;
  const requests = [];
  const sha = source => createHash('sha256').update(source).digest('hex');
  const source = `import Base
import ./helper.bend as H
import ./LAWS.bend as L

type Box is Data:
  Box{}

def helper() -> U32: 30
def main() -> U32: H.value(helper())
def unrelated() -> U32: 999
def L.claim(n): {==}
`;
  const liveHelper = 'import Base\n# WORKING_COPY_HELPER\ndef value(x: U32) -> U32: leaf(x)\n# WORKING_COPY_LEAF\ndef leaf(x: U32) -> U32: U32.add(x,2002)\n';
  try {
    await mkdir(join(root, 'src'));
    await writeFile(join(root, 'src/main.bend'), source);
    await writeFile(join(root, 'src/helper.bend'), 'import Base\n# STALE_COMMITTED_HELPER\ndef value(x: U32) -> U32: 1001\n');
    await writeFile(join(root, 'src/LAWS.bend'), 'import Base\nlaw claim:\n  for +n: U32\n  {n == n : U32}\n');
    await writeFile(join(root, 'src/unrelated.bend'), 'import Base\n# UNRELATED_OTHER_FILE\ndef value(x: U32) -> U32: 7777\n');
    await writeFile(join(root, 'src/types.bend'), 'type OnlyType is Data:\n  OnlyType{}\n');
    await writeFile(join(root, 'perch.yaml'), 'rules:\n  - name: fixture-method\n    where: "**/*.bend"\n    each: method\n    gate: false\n    ensure: This declaration preserves its stated contract using the supplied helper context.\n');
    const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
    git(['init', '-q', '-b', 'main']); git(['add', '.']);
    git(['-c', 'user.name=Bend unit test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Bend unit fixture']);
    await writeFile(join(root, 'src/helper.bend'), liveHelper);
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body);
      requests.push(body);
      const response = { model: 'offline-working-copy-only', answers: Object.fromEntries(Object.keys(body.questions).map(key => [key, { noul: body.state.name === 'unrelated' ? 0 : 1 }])) };
      return { ok: true, json: async () => response, clone: () => ({ json: async () => response }) };
    };
    const run = async (target, extra = []) => {
      const output = [], errors = [];
      const code = await runPerch(['check', target, '--rules', 'fixture-method', ...extra], { root,
        env: { PERCH_API_KEY: 'offline-fixture' }, stdout: text => output.push(text), stderr: text => errors.push(text) });
      return { code, errors: errors.join('\n'), result: output.length ? JSON.parse(output.join('\n')) : null };
    };
    const checked = await run('src/main.bend');
    assert.equal(checked.code, 3, checked.errors);
    assert.equal(checked.result.checked, 4);
    assert.deepEqual(checked.result.units.map(unit => unit.name), ['helper', 'main', 'unrelated', 'L.claim']);
    assert.equal(requests.length, 4, 'one model request per parsed declaration');
    for (const request of requests) {
      assert.ok(!request.state.file, 'this must be a method rule request');
      assert.match(request.state.source, new RegExp(`^def ${request.state.name.replaceAll('.', '\\.')}\\(`));
      assert.equal(request.state.source.split('\n').filter(line => line.startsWith('def ')).length, 1, 'unrelated declarations are not in the primary unit');
      assert.ok(!JSON.stringify(request.state).includes('STALE_COMMITTED_HELPER'));
      assert.ok(!JSON.stringify(request.state).includes('UNRELATED_OTHER_FILE'));
    }
    const main = requests.find(request => request.state.name === 'main').state;
    assert.deepEqual(main.calls.map(call => call.name), ['value', 'helper', 'leaf']);
    assert.ok(main.calls.some(call => call.source.includes('WORKING_COPY_HELPER')));
    assert.ok(main.calls.some(call => call.source.includes('WORKING_COPY_LEAF')));
    assert.ok(main.datatypes.some(type => type.name === 'Box'));
    const claim = requests.find(request => request.state.name === 'L.claim').state;
    assert.match(claim.laws[0].source, /^law claim:/);
    const unit = checked.result.units.find(unit => unit.name === 'main');
    assert.equal(unit.asked.length, 1);
    assert.equal(unit.context.basis, 'working-tree');
    assert.equal(unit.context.files.find(file => file.path === 'src/helper.bend').source_sha256, sha(liveHelper));
    assert.deepEqual(checked.result.broken.map(item => [item.name, item.line]), [['unrelated', 10]]);
    const beforeNamed = requests.length;
    const receiptDirectory = join(root, '.perch/usage');
    const previousReceipts = new Set(await readdir(receiptDirectory));
    const named = await run('src/main.bend::main');
    assert.equal(named.code, 0, named.errors);
    assert.equal(named.result.checked, 1);
    assert.equal(requests.length, beforeNamed + 1);
    const newReceipts = (await readdir(receiptDirectory)).filter(name => !previousReceipts.has(name));
    assert.equal(newReceipts.length, 1);
    const namedReceiptText = await readFile(join(receiptDirectory, newReceipts[0]), 'utf8');
    const namedReceipt = JSON.parse(namedReceiptText);
    assert.equal(namedReceipt.units.length, 1, 'a named check must retain its parsed unit and helper identities');
    const retainedUnit = namedReceipt.units[0];
    assert.equal(retainedUnit.name, 'main');
    assert.equal(retainedUnit.path, 'src/main.bend');
    assert.equal(retainedUnit.line, 9);
    assert.equal(retainedUnit.checked, 1);
    assert.equal(retainedUnit.asked[0].rule, 'fixture-method');
    assert.deepEqual(retainedUnit.context, named.result.context);
    assert.equal(retainedUnit.context.files.find(file => file.path === 'src/helper.bend').source_sha256, sha(liveHelper));
    assert.ok(!namedReceiptText.includes('WORKING_COPY_HELPER'), 'retain hashes, not helper source bodies');
    const beforeZero = requests.length;
    const zero = await run('src/types.bend');
    assert.equal(zero.code, 1);
    assert.equal(zero.result.checked, 0);
    assert.match(zero.errors, /no-coverage/);
    assert.equal(requests.length, beforeZero);
    await writeFile(join(root, 'src/helper.bend'), 'def value( -> U32: 0\n');
    const malformedHelper = await run('src/main.bend');
    assert.equal(malformedHelper.code, 1);
    assert.match(malformedHelper.errors, /context src\/helper.bend does not parse/);
    assert.equal(requests.length, beforeZero, 'all selected contexts preflight before any provider request');
    await writeFile(join(root, 'src/helper.bend'), liveHelper);
    let attempts = 0;
    globalThis.fetch = async () => {
      if (++attempts > 1) return { ok: false, status: 401, text: async () => 'offline provider failure' };
      const response = { model: 'offline-first-unit-only', answers: { 'fixture-method': { noul: 1 } } };
      return { ok: true, json: async () => response, clone: () => ({ json: async () => response }) };
    };
    const partial = await run('src/main.bend', ['--parallel', '1']);
    assert.equal(partial.code, 1);
    assert.equal(partial.result, null, 'an aggregate provider failure must not return the completed first unit as success');
    assert.equal(attempts, 2);
  } finally {
    globalThis.fetch = realFetch;
    await rm(root, { recursive: true, force: true });
  }
});

test('working-copy helper traversal is bounded and reports context limits', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-bend-context-'));
  try {
    const source = 'import Base\ndef leaf() -> U32: 1\ndef helper() -> U32: leaf()\ndef main() -> U32: helper()\n';
    const review = await createBendReview({ root, path: 'main.bend', source, analysis: await analyzeBendSource(source), limits: { helpers: 1 } });
    const context = await review.forUnit('main');
    assert.deepEqual(context.seen.calls.map(call => call.name), ['helper']);
    assert.equal(context.provenance.truncated, true);
    assert.equal(context.seen.context_notes.truncated, true);
    assert.equal(context.provenance.files.length, 1);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

async function datatypeFixture(t, files, limits = {}, snapshot = null) {
  const root = snapshot?.root ?? await mkdtemp(join(tmpdir(), 'knot-datatype-context-'));
  if (!snapshot) t.after(() => rm(root, { recursive: true, force: true }));
  for (const [path, source] of Object.entries(files)) await writeFile(join(root, path), source);
  const captured = snapshot ?? await createBendSourceSnapshot(root);
  const { source, analysis } = await captured.load('main.bend');
  assert.equal(analysis.parser_status, 'parsed', analysis.parser_message);
  const review = await createBendReview({ root, path: 'main.bend', source, analysis, snapshot: captured, limits });
  return { root, snapshot: captured, context: await review.forUnit('main') };
}

test('datatype context resolves supplied local types without turning them into callees', async t => {
  const { context } = await datatypeFixture(t, {
    'main.bend': 'import Base\ntype Payload is Type:\n  Owned{x: U32}\ndef helper(p: Payload) -> Payload: p\ndef main(p: Payload) -> Payload: helper(p)\n',
  });
  assert.deepEqual(context.seen.calls.map(x => x.name), ['helper']);
  assert.deepEqual(context.seen.datatypes.map(x => x.name), ['Payload']);
  assert.ok(!context.provenance.unresolved.some(x => x.name === 'Payload'));
  assert.equal(context.provenance.truncated, false);
  assert.deepEqual(context.builtin.callees.map(x => x.node.name), ['helper']);
});

test('explicit aliased datatype context includes transitive types, preserves snapshot and deduplicates cycles', async t => {
  const files = {
    'main.bend': 'import Base\nimport ./types.bend as T\ndef main(p: T.Box<U32>) -> T.Box<U32>: p\n',
    'types.bend': 'import Base\nimport ./leaf.bend as L\ntype Box<-A: Type> is Type:\n  Wrap{item: A, rest: L.Leaf}\n',
    'leaf.bend': 'import Base\nimport ./types.bend as Again\ntype Leaf is Type:\n  End{}\n  Next{owner: Again.Box<U32>}\n',
  };
  const first = await datatypeFixture(t, files, { files: 3, helpers: 2 });
  assert.deepEqual(first.context.provenance.files.map(x => x.path), ['leaf.bend', 'main.bend', 'types.bend']);
  assert.deepEqual(first.context.seen.datatypes.map(x => x.name).sort(), ['Box', 'Leaf']);
  assert.ok(first.context.seen.datatypes.find(x => x.name === 'Box').source.includes('item: A'));
  assert.ok(!first.context.provenance.unresolved.some(x => ['T.Box', 'L.Leaf', 'Again.Box', 'A'].includes(x.name)));
  assert.equal(first.context.provenance.truncated, false);
  assert.deepEqual(first.context.seen.calls, []);
  assert.equal(first.snapshot.stats.parse_calls, 3);
  const oldHash = first.context.provenance.files.find(x => x.path === 'leaf.bend').source_sha256;
  const changed = { 'leaf.bend': files['leaf.bend'].replace('End{}', 'End{value: U32}') };
  const retained = await datatypeFixture(t, changed, { files: 3, helpers: 2 }, first.snapshot);
  assert.deepEqual(retained.context, first.context, 'same command never refreshes one type dependency');
  const fresh = await createBendSourceSnapshot(first.root);
  const updated = await datatypeFixture(t, {}, {}, fresh);
  assert.notEqual(updated.context.provenance.files.find(x => x.path === 'leaf.bend').source_sha256, oldHash);
  assert.equal(await readFile(join(first.root, 'leaf.bend'), 'utf8'), changed['leaf.bend'], 'review leaves source unchanged');
});

test('missing imports and missing datatype declarations remain explicit; malformed imported types reject', async t => {
  const { root, context } = await datatypeFixture(t, {
    'main.bend': 'import Base\nimport ./types.bend as T\nimport ./absent.bend as Missing\ndef main(x: T.Absent, y: Missing.Type) -> U32: 0\n',
    'types.bend': 'import Base\ntype Present is Data:\n  Present{}\n',
  });
  assert.ok(context.provenance.unresolved.some(x => x.name === 'T.Absent' && x.reason === 'declaration-not-in-import'));
  assert.ok(context.provenance.unresolved.some(x => x.name === 'Missing.Type' && x.reason === 'unavailable-local-import:ENOENT'));
  assert.ok(!context.seen.datatypes.some(x => x.name === 'Absent'));
  assert.ok(context.provenance.files.some(x => x.path === 'types.bend'), 'negative lookup retains the inspected file identity');
  await writeFile(join(root, 'types.bend'), 'import Base\ntype Present is Data:\n  Present{broken:}\n');
  const snapshot = await createBendSourceSnapshot(root);
  await assert.rejects(datatypeFixture(t, {}, {}, snapshot), /context types.bend does not parse/);
});

test('parsed generic datatype context preserves AST spans and existing function graph references', async t => {
  const source = 'import Base\ntype Box<q, -A: Kind(q)> is Kind(q):\n  Box{item: A}\ndef main(x: +Box<U32>) -> +Box<U32>: x\n';
  const parsed = await analyzeBendSource(source);
  assert.equal(parsed.parser_status, 'parsed');
  assert.ok(!parsed.references.some(x => x.name === 'Box'), 'generic datatype metadata must not add function graph edges');
  assert.deepEqual(parsed.references.filter(x => x.source === 'bend:main').map(x => x.name), ['U32', 'U32']);
  assert.equal(parsed.declarations.length, 1, 'datatype is not a new function/law target');
  const types = parsed.declarations[0].context_references;
  assert.deepEqual(types.map(x => x.name), ['Box', 'Box']);
  assert.ok(types.every(x => Buffer.from(source).subarray(x.location.start.byte, x.location.end.byte).toString() === '+Box<U32>'));
  const { context } = await datatypeFixture(t, { 'main.bend': source });
  assert.deepEqual(context.seen.datatypes.map(x => x.name), ['Box']);
  assert.ok(!context.provenance.unresolved.some(x => ['Box', 'A', 'q'].includes(x.name)));
});

test('datatype dependency file, helper and byte caps stay fail closed', async t => {
  const files = {
    'main.bend': 'import Base\nimport ./first.bend as F\ndef main(x: F.First) -> F.First: x\n',
    'first.bend': 'import Base\nimport ./second.bend as S\ntype First is Type:\n  First{next: S.Second}\n',
    'second.bend': 'import Base\ntype Second is Type:\n  Second{x: U32}\n',
  };
  for (const limits of [{ files: 2 }, { helpers: 1 }, { bytes: 1 }]) {
    const { context } = await datatypeFixture(t, files, limits);
    assert.equal(context.provenance.truncated, true, JSON.stringify(limits));
    assert.ok(context.provenance.unresolved.length > 0, 'the omitted collaborator remains explicit');
    assert.ok(!context.seen.datatypes.some(x => x.name === 'Second'), JSON.stringify(limits));
  }
});

test('direct datatype style context retains one-file cap and composition checks explicit type dependencies', async t => {
  const { root } = await datatypeFixture(t, {
    'main.bend': 'import Base\nimport ./types.bend as T\ntype Local is Type:\n  Local{next: T.Imported}\ndef main(x: Local) -> Local: x\n',
    'types.bend': 'import Base\ntype Imported is Type:\n  Imported{x: U32}\n',
  });
  const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
  const selected = await prepareStyleTargets(['main.bend::Local'], 'Preserve the owner', config, root);
  assert.equal(selected[0].context.limits.files, 1, 'do not widen the datatype style scope');
  assert.equal(selected[0].context.truncated, true);
  assert.ok(selected[0].context.unresolved.some(x => x.name === 'T.Imported' && x.reason === 'context-file-limit'));
  assert.deepEqual(selected[0].state.called_by.map(x => x.name), ['main']);
  assert.ok(!selected[0].state.datatypes.some(x => x.name === 'Local'), 'primary datatype is already the reviewed source');
  const missing = await prepareStyleComposition(selected, 'Preserve the owner', config, root);
  assert.equal(missing.available, false);
  assert.ok(missing.candidate.context.unresolved.some(x => x.name === 'T.Imported' && x.reason === 'collaborator-not-in-group'));
  const complete = await prepareStyleTargets(['main.bend::Local', 'types.bend::Imported'], 'Preserve the owner', config, root);
  const composition = await prepareStyleComposition(complete, 'Preserve the owner', config, root);
  assert.equal(composition.available, true, 'explicit complete group resolves type dependencies without a larger file cap');
  assert.deepEqual(composition.candidate.context.unresolved, []);
});

test('real CLI parses Bend-only scans, imports and method targets; syntax failure sends no model request', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-bend-cli-'));
  const realFetch = globalThis.fetch;
  const requests = [];
  try {
    await mkdir(join(root, 'src'));
    await writeFile(join(root, 'src/helper.bend'), 'import Base\ndef identity(x: U32) -> U32: x\n');
    await writeFile(join(root, 'src/main.bend'), 'import Base\nimport ./helper.bend as H\ndef main() -> U32: H.identity(42)\n');
    await writeFile(join(root, 'note.md'), '# No applicable rules\n');
    await writeFile(join(root, 'perch.yaml'), 'scan_types: [defect, lint]\nrules:\n  - name: fixture-contract\n    where: "**/*.bend"\n    each: method\n    gate: false\n    ensure: Returns the stated input or the stated constant.\n  - name: fixture-file\n    where: "**/*.bend"\n    each: file\n    gate: false\n    ensure: This is a small fixture.\n');
    const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
    git(['init', '-q', '-b', 'main']); git(['add', '.']);
    git(['-c', 'user.name=Bend parser test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Bend fixture']);
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); requests.push(body);
      const answers = Object.fromEntries(Object.entries(body.questions).map(([key, q]) => {
        if (q.type === 'noul') return [key, { noul: key.startsWith('fixture-') || key === 'does_what_it_claims' ? 1 : 0 }];
        if (q.type === 'score') return [key, { score: 0, confidence: 1, probabilities: Object.fromEntries(q.criteria.map((_, i) => [i, i === 0 ? 1 : 0])) }];
        const choice = Object.keys(q.criteria).at(-1);
        return [key, { choice, confidence: 1, probabilities: { [choice]: 1 } }];
      }));
      const response = { model: 'offline-integration-only', answers };
      return { ok: true, json: async () => response, clone: () => ({ json: async () => response }) };
    };
    const run = async args => {
      const output = [], errors = [];
      const code = await runPerch(args, { root, env: { PERCH_API_KEY: 'offline-fixture' },
        stdout: t => output.push(t), stderr: t => errors.push(t) });
      return { code, output: output.join('\n'), errors: errors.join('\n') };
    };
    const method = await run(['check', 'src/main.bend::main', '--rules', 'fixture-contract']);
    assert.equal(method.code, 0, method.errors);
    const checked = JSON.parse(method.output);
    assert.equal(checked.checked, 1);
    assert.equal(checked.name, 'main');
    assert.equal(checked.line, 3);
    assert.equal(checked.parser.status, 'parsed');
    const file = await run(['check', 'src/main.bend', '--rules', 'fixture-file']);
    assert.equal(file.code, 0, file.errors);
    assert.equal(JSON.parse(file.output).parser.declarations, 1);
    const scan = await run(['scan', '--out', join(root, '.perch'), '--json']);
    assert.equal(scan.code, 0, scan.errors);
    const result = JSON.parse(scan.output);
    assert.equal(result.parser_coverage.supported, 2);
    assert.equal(result.parser_coverage.parsed, 2);
    assert.equal(result.parser_coverage.parse_failures, 0);
    assert.equal(result.run.methods, 2);
    assert.equal(result.run.edges, 1);
    assert.ok(result.run.calls > 0);
    assert.ok(requests.some(request => request.state?.name === 'main'
      && request.state.calls?.some(call => call.name === 'identity')), 'committed method-rule scans include graph neighbors too');
    const noCoverage = await run(['scan', '--paths', 'note.md', '--out', join(root, '.perch'), '--json']);
    assert.equal(noCoverage.code, 1, 'a successful scan of zero methods and zero file rules is not coverage');
    assert.match(noCoverage.errors, /no-coverage/);
    const before = requests.length;
    await writeFile(join(root, 'src/main.bend'), 'def main( -> U32: 42\n');
    const malformed = await run(['check', 'src/main.bend', '--rules', 'fixture-file']);
    assert.equal(malformed.code, 1);
    assert.match(malformed.errors, /does not parse/);
    assert.equal(requests.length, before);
    git(['add', 'src/main.bend']);
    git(['-c', 'user.name=Bend parser test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Intentional parse error']);
    const partial = await run(['scan', '--out', join(root, '.perch'), '--json']);
    assert.equal(partial.code, 1, partial.errors);
    assert.equal(JSON.parse(partial.output).parser_coverage.parse_failures, 1);
    assert.match(partial.errors, /partial-parser-coverage/);
    // The native command uses the same patched bundle, not just the wrapper.
    const { knotResolveModule, knotCreateSourceAnalyzer, knotBuildGraph } = await import('../node_modules/@lakeday/perch/dist/cli.mjs');
    assert.equal(knotResolveModule('src/main.bend', './helper.bend', 'bend', new Set(['src/helper.bend'])), 'src/helper.bend');
    assert.equal(knotResolveModule('src/main.bend', '0x1234/helper.bend', 'bend', new Set()), null);
    assert.equal((await knotCreateSourceAnalyzer().analyzeSource('function f() { return 1; }', 'javascript')).parser_status, 'parsed');
    const methodRow = (path, name) => ({ id: `${path}::${name}`, name, qualified_name: name, line: 1, end_line: 1 });
    const graph = knotBuildGraph([
      { path: 'main.bend', language: 'bend', methods: [methodRow('main.bend', 'main'), methodRow('main.bend', 'id')],
        calls: ['H.Namespace.id', 'Missing.id', 'Unknown.id'].map(name => ({ name, from: 'main.bend::main', line: 1 })),
        values: [{ name: 'Other.unique', from: 'main.bend::main', line: 1 }],
        imports: [{ alias: 'H', name: '*', module: './helper.bend' }, { alias: 'Missing', name: '*', module: './absent.bend' }] },
      { path: 'helper.bend', language: 'bend', methods: [methodRow('helper.bend', 'Namespace.id'), methodRow('helper.bend', 'unique')], calls: [], values: [], imports: [] },
    ]);
    assert.deepEqual(graph.callees('main.bend::main'), ['helper.bend::Namespace.id'], 'unresolved Bend names never fall back to unrelated tail/unique names');
  } finally {
    globalThis.fetch = realFetch;
    await rm(root, { recursive: true, force: true });
  }
});

test('scan parser coverage follows configured selection while retaining required imports and caller context', async t => {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-coverage-'));
  const originalFetch = globalThis.fetch;
  t.after(async () => { globalThis.fetch = originalFetch; await rm(root, { recursive: true, force: true }); });
  await mkdir(join(root, 'ignored'));
  await mkdir(join(root, 'ignored/deep'));
  await mkdir(join(root, 'other'));
  await mkdir(join(root, 'aaa'));
  await mkdir(join(root, 'ignoredness'));
  await mkdir(join(root, 'single/deep'), { recursive: true });
  await mkdir(join(root, 'misc'));
  for (let i = 0; i < 21; i++) await writeFile(join(root, `aaa/data-${i}.bend`), 'type Token is Data:\n  Token{}\n');
  const config = 'scan_types: [defect, security, lint]\nignore: ["ignored/**", "single/*.bend", "**/notes-*.bend"]\nrules: []\n';
  await writeFile(join(root, 'perch.yaml'), config);
  await writeFile(join(root, 'ignoredness/value.bend'), 'import Base\ndef neighbor() -> U32: 1\n');
  await writeFile(join(root, 'ignored.bend'), 'import Base\ndef direct_file() -> U32: 2\n');
  await writeFile(join(root, 'ignored/direct.bend'), 'import Base\ndef hidden_direct() -> U32: 3\n');
  await writeFile(join(root, 'single/direct.bend'), 'import Base\ndef single_hidden() -> U32: 4\n');
  await writeFile(join(root, 'single/deep/value.bend'), 'import Base\ndef single_nested() -> U32: 5\n');
  await writeFile(join(root, 'misc/notes-hidden.bend'), 'import Base\ndef prefix_hidden() -> U32: 6\n');
  await writeFile(join(root, 'main.bend'), 'import Base\nimport ./ignored/deep/helper.bend as H\ndef main() -> U32: H.identity(42)\n');
  await writeFile(join(root, 'ignored/deep/helper.bend'), 'import Base\ndef identity(x: U32) -> U32: x\n');
  await writeFile(join(root, 'ignored/deep/bad.bend'), 'def bad( -> U32: 1\n');
  await writeFile(join(root, 'other/bad.bend'), 'def bad( -> U32: 2\n');
  const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
  const commit = message => {
    git(['add', '.']);
    git(['-c', 'user.name=Coverage test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', message]);
  };
  git(['init', '-q', '-b', 'main']); commit('coverage fixture');
  const requests = [];
  globalThis.fetch = async (_url, options) => {
    const body = JSON.parse(options.body); requests.push(body);
    const answers = Object.fromEntries(Object.entries(body.questions).map(([key, question]) => {
      if (question.type === 'noul') return [key, { noul: key === 'does_what_it_claims' ? 1 : 0 }];
      if (question.type === 'score') return [key, { score: 0, confidence: 1,
        probabilities: Object.fromEntries(question.criteria.map((_, i) => [i, i === 0 ? 1 : 0])) }];
      const choice = Object.keys(question.criteria).at(-1);
      return [key, { choice, confidence: 1, probabilities: { [choice]: 1 } }];
    }));
    const response = { model: 'offline-coverage-only', answers };
    return { ok: true, json: async () => response, clone: () => ({ json: async () => response }) };
  };
  const run = async extra => {
    const output = [], errors = [];
    const code = await runPerch(['scan', '--json', ...extra], { root, env: { PERCH_API_KEY: 'offline-fixture' },
      stdout: text => output.push(text), stderr: text => errors.push(text) });
    return { code, errors: errors.join('\n'), result: JSON.parse(output.join('\n')) };
  };
  const selected = await run(['--paths', 'main.bend']);
  assert.equal(selected.code, 0, selected.errors);
  assert.equal(selected.result.run.methods, 1);
  assert.equal(selected.result.parser_coverage.supported, 2);
  assert.equal(selected.result.parser_coverage.parse_failures, 0);
  assert.deepEqual(selected.result.parser_coverage.context_dependencies, ['ignored/deep/helper.bend']);
  assert.equal(selected.result.run.analysis_coverage.parse_failures, 2);
  assert.equal(selected.result.run.analysis_coverage.parser_diagnostics_capped, true);
  assert.equal(selected.result.run.analysis_coverage.parser_diagnostics.length, 20);
  assert.ok(selected.result.run.analysis_coverage.parser_diagnostics.every(file => file.status === 'parsed'));
  assert.deepEqual(selected.result.run.analysis_coverage.failed_files.map(file => file.path), ['ignored/deep/bad.bend', 'other/bad.bend'],
    'the complete failure list does not disappear behind the first twenty successful diagnostics');
  assert.ok(requests.some(request => request.state.calls?.some(call => call.name === 'identity')),
    'ignored helper remains in actual supplied source context');
  const whole = await run([]);
  assert.equal(whole.code, 1, 'unignored malformed source still blocks a whole scan');
  assert.deepEqual(whole.result.run.visited.map(method => method.path).sort(),
    ['ignored.bend', 'ignoredness/value.bend', 'main.bend', 'single/deep/value.bend'],
    'recursive ignores respect directory boundaries; single stars and **/ prefixes retain their existing scope');
  assert.equal(whole.result.parser_coverage.parse_failures, 1);
  assert.deepEqual(whole.result.parser_coverage.failed_files.map(file => file.path), ['other/bad.bend']);
  await writeFile(join(root, 'perch.yaml'), 'scan_types: [defect, security, lint]\nrules: []\n');
  const changedSelection = await run([]);
  assert.equal(changedSelection.result.parser_coverage.parse_failures, 2,
    'working-copy ignore selection is applied again even when committed analysis is cached');
  await writeFile(join(root, 'perch.yaml'), config);
  await writeFile(join(root, 'ignored/deep/helper.bend'), 'def identity( -> U32: 3\n');
  commit('malformed imported dependency');
  const imported = await run(['--paths', 'main.bend']);
  assert.equal(imported.code, 1);
  assert.deepEqual(imported.result.parser_coverage.failed_files.map(file => file.path), ['ignored/deep/helper.bend']);
  await writeFile(join(root, 'ignored/deep/helper.bend'), 'import Base\ndef identity(x: U32) -> U32: x\n');
  await writeFile(join(root, 'ignored/caller.bend'),
    'import Base\nimport ../main.bend as M\nimport ../other/bad.bend as B\ndef context() -> U32: U32.add(M.main(),B.value())\n');
  commit('caller context has malformed dependency');
  const caller = await run(['--paths', 'main.bend']);
  assert.equal(caller.code, 1);
  assert.ok(caller.result.parser_coverage.context_dependencies.includes('ignored/caller.bend'));
  assert.deepEqual(caller.result.parser_coverage.failed_files.map(file => file.path), ['other/bad.bend']);
});

test('parallel file checks preserve requests and ordering, isolate budgets, refresh rules and drain failures', async t => {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-parallel-'));
  const originalFetch = globalThis.fetch;
  t.after(async () => { globalThis.fetch = originalFetch; await rm(root, { recursive: true, force: true }); });
  await mkdir(join(root, 'src'));
  await writeFile(join(root, 'src/main.bend'), 'import Base\n' + Array.from({ length: 80 }, (_, i) => `def f${i}() -> U32: ${i}\n`).join(''));
  const rule = text => `rules:\n  - name: fixture\n    where: '**/*.bend'\n    each: method\n    ensure: ${text}\n`;
  await writeFile(join(root, 'perch.yaml'), rule('first snapshot'));
  const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
  git(['init', '-q', '-b', 'main']); git(['add', '.']);
  git(['-c', 'user.name=Perch concurrency fixture', '-c', 'user.email=test@example.invalid', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture']);
  const run = async jobs => {
    const output = [], errors = [];
    const code = await runPerch(['check', 'src/main.bend', '--parallel', String(jobs), '--rules', 'fixture'], {
      root, env: { PERCH_API_KEY: 'offline-fixture' }, stdout: text => output.push(text), stderr: text => errors.push(text),
    });
    return { code, result: output.length ? JSON.parse(output.join('\n')) : null, errors };
  };
  let requests = [], active = 0, peak = 0;
  globalThis.fetch = async (_url, init) => {
    const body = JSON.parse(init.body); requests.push(body); peak = Math.max(peak, ++active);
    await new Promise(resolve => setTimeout(resolve, body.state.name === 'f1' ? 15 : 1));
    active--;
    const answer = { model: 'offline-parallel', answers: { fixture: { noul: body.state.name === 'f7' ? 0 : 1 } } };
    return { ok: true, json: async () => answer, clone: () => ({ json: async () => answer }) };
  };
  const serial = await run(1), originalRequests = requests;
  requests = []; peak = 0;
  const parallel = await run(8);
  assert.equal(serial.code, 3); assert.equal(parallel.code, 3);
  assert.equal(parallel.result.checked, 80, 'file size must not consume the 64-request allowance of a single declaration');
  assert.deepEqual(parallel.result, serial.result, 'scheduling must not change the full result');
  assert.deepEqual(requests.sort((a,b) => a.state.name.localeCompare(b.state.name)), originalRequests.sort((a,b) => a.state.name.localeCompare(b.state.name)));
  assert.equal(peak, 8); assert.equal(active, 0);
  assert.deepEqual(parallel.result.broken.map(x => x.name), ['f7']);
  let edited = false;
  globalThis.fetch = async (_url, init) => {
    const body = JSON.parse(init.body);
    assert.match(JSON.stringify(body.questions.fixture), /first snapshot/);
    if (!edited) { edited = true; await writeFile(join(root, 'perch.yaml'), rule('next command snapshot')); }
    const answer = { model: 'offline-snapshot', answers: { fixture: { noul: 1 } } };
    return { ok: true, json: async () => answer, clone: () => ({ json: async () => answer }) };
  };
  assert.equal((await run(8)).code, 0, 'every unit uses the command snapshot');
  let attempts = 0, finished = 0;
  globalThis.fetch = async (_url, init) => {
    const body = JSON.parse(init.body);
    assert.match(JSON.stringify(body.questions.fixture), /next command snapshot/);
    attempts++;
    if (body.state.name === 'f1') return { ok: false, status: 401, text: async () => 'fixture denial' };
    await new Promise(resolve => setTimeout(resolve, 10)); finished++;
    const answer = { model: 'offline-drain', answers: { fixture: { noul: 1 } } };
    return { ok: true, json: async () => answer, clone: () => ({ json: async () => answer }) };
  };
  const failed = await run(4);
  assert.equal(failed.code, 1); assert.equal(failed.result, null);
  assert.ok(attempts <= 5, `failure must stop new dispatch (${attempts})`);
  assert.equal(finished, attempts - 1, 'already-issued work is drained before the wrapper releases its meter');
  const before = attempts;
  assert.equal((await run(257)).code, 1);
  assert.equal(attempts, before, 'invalid concurrency fails before a paid request');
});

test('built-in proof requests include the selected working-copy law once and change identity with it', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-proof-context-'));
  const previousFetch = globalThis.fetch, requests = [];
  const proof = 'import Base\nimport ./LAWS.bend as L\ndef L.claim(n): {==}\n';
  const oldLaw = 'import Base\nlaw claim:\n  for -n: U32\n  {n == n : U32}\n';
  const newLaw = oldLaw.replace('{n == n : U32}', '{U32.add(n,0) == n : U32}');
  const sha = value => createHash('sha256').update(value).digest('hex');
  let changeAfterFirstRequest = true;
  try {
    await writeFile(join(root, 'PROOF.bend'), proof);
    await writeFile(join(root, 'LAWS.bend'), oldLaw);
    await writeFile(join(root, 'perch.yaml'), 'rules:\n  - name: fixture-proof\n    where: "**/*.bend"\n    each: method\n    gate: false\n    ensure: Fills its paired law.\n');
    const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
    git(['init', '-q']); git(['add', '.']);
    git(['-c', 'user.name=Proof fixture', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Proof fixture']);
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); requests.push(body);
      if (changeAfterFirstRequest) {
        changeAfterFirstRequest = false;
        await writeFile(join(root, 'LAWS.bend'), newLaw);
      }
      const answers = Object.fromEntries(Object.entries(body.questions).map(([key, q]) => {
        if (q.type === 'noul') return [key, { noul: key === 'fixture-proof' || key === 'does_what_it_claims' ? 1 : 0 }];
        if (q.type === 'score') return [key, { score: 0, confidence: 1, probabilities: Object.fromEntries(q.criteria.map((_, i) => [i, i === 0 ? 1 : 0])) }];
        const choice = Object.keys(q.criteria).at(-1);
        return [key, { choice, confidence: 1, probabilities: { [choice]: 1 } }];
      }));
      const response = { model: 'offline-proof-context-only', answers };
      return { ok: true, json: async () => response, clone: () => ({ json: async () => response }) };
    };
    const run = async target => {
      const output = [], errors = [], start = requests.length;
      const code = await runPerch(['check', target, '--parallel', '1'], { root,
        env: { PERCH_API_KEY: 'offline-fixture' }, stdout: text => output.push(text), stderr: text => errors.push(text) });
      assert.ok([0, 3].includes(code), errors.join('\n'));
      return { result: JSON.parse(output.join('\n')), requests: requests.slice(start) };
    };
    const first = await run('PROOF.bend::L.claim');
    assert.ok(first.result.checked >= 2, 'nonzero custom and built-in coverage');
    assert.equal(first.requests.length, 2);
    const firstCustom = first.requests.find(request => !request.state.method);
    const firstBuiltin = first.requests.find(request => request.state.method);
    assert.ok(firstCustom && firstBuiltin, 'capture both actual checkTarget paths');
    assert.deepEqual(firstBuiltin.state.laws, firstCustom.state.laws);
    assert.equal(firstBuiltin.state.laws.length, 1);
    assert.equal(firstBuiltin.state.laws[0].source, oldLaw.slice(oldLaw.indexOf('law')).trimEnd());
    assert.deepEqual(firstBuiltin.state.context_notes, firstCustom.state.context_notes);
    assert.equal(firstBuiltin.state.context_notes.truncated, false);
    assert.equal(first.result.context.files.find(file => file.path === 'LAWS.bend').source_sha256, sha(oldLaw),
      'preflight snapshot survives a file edit between custom and built-in requests');
    assert.equal(firstBuiltin.state.calls.length, 0, 'the paired law is not a fabricated callee');
    assert.ok(!Object.keys(firstBuiltin.questions).some(key => key.startsWith('misuse_')));
    const second = await run('PROOF.bend::L.claim');
    const secondBuiltin = second.requests.find(request => request.state.method);
    assert.equal(secondBuiltin.state.laws[0].source, newLaw.slice(newLaw.indexOf('law')).trimEnd());
    assert.equal(second.result.context.files.find(file => file.path === 'LAWS.bend').source_sha256, sha(newLaw));
    assert.equal(secondBuiltin.state.method.source, firstBuiltin.state.method.source);
    assert.deepEqual(secondBuiltin.questions, firstBuiltin.questions);
    assert.equal(await readFile(join(root, 'PROOF.bend'), 'utf8'), proof);
    const { knotAskKey } = await import('../node_modules/@lakeday/perch/dist/cli.mjs');
    const cacheKey = request => knotAskKey([{ state: request.state, questions: request.questions }], [], 'offline-fixed-client');
    const stored = new Map([[cacheKey(firstBuiltin), 'old-law-answer']]);
    assert.notEqual(cacheKey(firstBuiltin), cacheKey(secondBuiltin));
    assert.equal(stored.get(cacheKey(secondBuiltin)), undefined, 'actual installed key cannot reuse the old-law answer');
    assert.equal(cacheKey(secondBuiltin), cacheKey(structuredClone(secondBuiltin)), 'identical input retains its identity');

    const local = 'import Base\ntype Marker is Data:\n  Marker{}\nlaw claim:\n  for -n: U32\n  {n == n : U32}\ndef unrelated() -> U32: 7\ndef claim(n): {==}\n';
    await writeFile(join(root, 'local.bend'), local);
    const localRun = await run('local.bend::claim');
    const localBuiltin = localRun.requests.find(request => request.state.method);
    const localCustom = localRun.requests.find(request => !request.state.method);
    assert.deepEqual(localBuiltin.state.laws, localCustom.state.laws);
    assert.equal(localBuiltin.state.laws.length, 1);
    assert.ok(!localBuiltin.state.module_scope.includes('law claim'), 'no line-tagged duplicate in module scope');
    assert.ok(!localBuiltin.state.module_scope.includes('{n == n'), 'the assertion is not duplicated either');
    assert.match(localBuiltin.state.module_scope, /type Marker/);
    assert.ok(!localBuiltin.state.method.source.includes('def unrelated'));
  } finally {
    globalThis.fetch = previousFetch;
    await rm(root, { recursive: true, force: true });
  }
});

test('paired-law omission and missing imports remain explicit without changing selection budgets', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-proof-limits-'));
  const source = 'import Base\nimport ./LAWS.bend as L\ndef L.claim(n): {==}\n';
  const law = 'import Base\nlaw claim:\n  for -n: U32\n  {n == n : U32}\n';
  try {
    await writeFile(join(root, 'LAWS.bend'), law);
    const prepare = async (text = source, limits = {}) => (await createBendReview({ root, path: 'PROOF.bend',
      source: text, analysis: await analyzeBendSource(text), limits })).forUnit(text === source ? 'L.claim' : 'main');
    const full = await prepare();
    const lawBytes = Buffer.byteLength(full.seen.laws[0].source);
    const exact = await prepare(source, { bytes: lawBytes });
    const short = await prepare(source, { bytes: lawBytes - 1 });
    assert.deepEqual(exact.builtin.paired_law_context.laws, full.seen.laws);
    assert.equal(exact.provenance.truncated, false);
    assert.deepEqual(short.builtin.paired_law_context.laws, []);
    assert.equal(short.builtin.paired_law_context.context_notes.truncated, true);
    assert.equal(short.provenance.limits.bytes, lawBytes - 1);
    assert.deepEqual(short.builtin.callees, full.builtin.callees);
    const helper = 'import Base\nlaw claim:\n  for -n: U32\n  {n == n : U32}\ndef claim(n): {==}\ndef main() -> U32: claim(1)\n';
    const omittedHelperLaw = await prepare(helper, { bytes: Buffer.byteLength('def claim(n): {==}') });
    assert.equal(omittedHelperLaw.builtin.paired_law_context.context_notes.truncated, true,
      'an ordinary target still reports an attempted helper-law omission');
    await rm(join(root, 'LAWS.bend'));
    const missing = await prepare();
    assert.deepEqual(missing.builtin.paired_law_context.laws, []);
    assert.ok(missing.builtin.paired_law_context.context_notes.unresolved.some(item => /unavailable-local-import/.test(item.reason)));
    await writeFile(join(root, 'LAWS.bend'), 'def malformed( -> U32: 1\n');
    await assert.rejects(prepare(), /does not parse/);
  } finally { await rm(root, { recursive: true, force: true }); }
});

test('paired laws stay inside every built-in token budget, chunk and retry preparation', async () => {
  const { knotMethodSteps, knotMethodStep, knotEstimateTokens } = await import('../node_modules/@lakeday/perch/dist/cli.mjs');
  const source = 'def claim(n):\n' + Array.from({ length: 180 }, (_, i) => `  let a${i} = U32.add(n,${i})`).join('\n') + '\n  {==}';
  const lines = source.split('\n');
  const node = { id: 'proof.bend::claim', qualified_name: 'claim', path: 'proof.bend', line: 1, end_line: lines.length };
  const law = { name: 'claim', path: 'laws.bend', line: 1, end_line: 3, source: 'law claim:\n  for -n: U32\n  {n == n : U32}' };
  const knotPairedLawContext = { laws: [law], context_notes: { basis: 'working-tree', unresolved: [], truncated: false } };
  const args = { node, lines, callees: [], callers: [], knotPairedLawContext };
  let chunked = false;
  for (const budget of [24000, 1600, 1000, 700]) {
    const steps = knotMethodSteps({ ...args, budget });
    chunked ||= steps.length > 1;
    for (const step of steps) {
      assert.deepEqual(step.state.laws, [law]);
      assert.ok(knotEstimateTokens(step.state) <= budget, 'law text is included before the budget check');
      assert.equal(JSON.stringify(step.state).split('law claim:').length - 1, 1);
    }
  }
  assert.ok(chunked, 'the regression must exercise nonzero multi-chunk preparation');
  const hugeLaw = { ...law, source: law.source + '\n# ' + 'contract '.repeat(2000) };
  assert.throws(() => knotMethodSteps({ ...args, lines: ['def claim(n): {==}'], node: { ...node, end_line: 1 },
    knotPairedLawContext: { ...knotPairedLawContext, laws: [hugeLaw] }, budget: 700 }), /exceeds the token budget/,
  'an oversized required law fails instead of vanishing when source chunks shrink');
  const localLines = ['law claim:', '  for -n: U32', '  {n == n : U32}', 'def claim(n): {==}'];
  const localLaw = { ...law, path: node.path };
  const localStep = knotMethodStep({ ...args, node: { ...node, line: 4, end_line: 4 }, lines: localLines,
    knotPairedLawContext: { ...knotPairedLawContext, laws: [localLaw] } });
  assert.equal(localStep.state.module_scope, null, 'direct methodStep default excludes the same local law too');
  assert.deepEqual(localStep.state.laws, [localLaw]);
  const ordinary = knotMethodSteps({ node, lines, callees: [], callers: [] });
  const absent = knotMethodSteps({ node, lines, callees: [], callers: [], knotPairedLawContext: undefined });
  assert.deepEqual(absent, ordinary, 'absent optional context leaves the legacy state/question shape untouched');
  assert.ok(ordinary.every(step => !('laws' in step.state) && !('context_notes' in step.state)));
});
