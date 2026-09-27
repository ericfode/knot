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
import { createBendReview } from '../scripts/perch-bend-context.mjs';

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
