import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
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
    const run = async target => {
      const output = [], errors = [];
      const code = await runPerch(['check', target, '--rules', 'fixture-method'], { root,
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
    const named = await run('src/main.bend::main');
    assert.equal(named.code, 0, named.errors);
    assert.equal(named.result.checked, 1);
    assert.equal(requests.length, beforeNamed + 1);
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
    const partial = await run('src/main.bend');
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
