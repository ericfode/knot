import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { main, knotCachedAnalyzer } from '../node_modules/@lakeday/perch/dist/cli.mjs';

const methodRule = name => ({ name, where: '**/*.bend', each: 'method', ensure: 'Returns the stated value.' });
const answer = body => ({ model: 'offline-incremental', answers: Object.fromEntries(Object.entries(body.questions).map(([name, q]) => {
  if (q.type === 'noul') return [name, { noul: name.startsWith('fixture') ? 1 : 0 }];
  if (q.type === 'score') return [name, { score: 0, confidence: 1,
    probabilities: Object.fromEntries(q.criteria.map((_, i) => [i, i === 0 ? 1 : 0])) }];
  const choice = Object.keys(q.criteria).at(-1);
  return [name, { choice, confidence: 1, probabilities: { [choice]: 1 } }];
})) });

async function fixture(t, rules = [methodRule('fixture')]) {
  const root = await mkdtemp(join(tmpdir(), 'knot-incremental-'));
  const originalFetch = globalThis.fetch, originalCwd = process.cwd();
  t.after(async () => { globalThis.fetch = originalFetch; process.chdir(originalCwd); await rm(root, { recursive: true, force: true }); });
  await mkdir(join(root, 'src'));
  await writeFile(join(root, '.gitignore'), '.perch/\n');
  await writeFile(join(root, 'src/helper.bend'), 'import Base\ndef value(x: U32) -> U32: U32.add(x, 1)\n');
  await writeFile(join(root, 'src/main.bend'), 'import Base\nimport ./helper.bend as H\ndef main() -> U32: H.value(42)\n');
  await writeFile(join(root, 'src/other.bend'), 'import Base\ndef other() -> U32: 7\n');
  const configure = async next => writeFile(join(root, 'perch.yaml'), JSON.stringify({ scan_types: [], rules: next }));
  await configure(rules);
  const git = args => execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  git(['init', '-q', '-b', 'main']);
  const commit = () => {
    git(['add', '.']);
    git(['-c', 'user.name=Incremental fixture', '-c', 'user.email=test@example.invalid', '-c', 'core.hooksPath=/dev/null',
      '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture']);
    return git(['rev-parse', 'HEAD']);
  };
  commit();
  const run = async ({ args = ['--incremental'], respond = answer, env = {} } = {}) => {
    const requests = [], output = [], errors = [];
    globalThis.fetch = async (_url, options) => {
      const body = JSON.parse(options.body); requests.push(body);
      return new Response(JSON.stringify(await respond(body)), { status: 200 });
    };
    process.chdir(root);
    try {
      const code = await main(['scan', '--json', ...args], { env: { PERCH_API_KEY: 'offline', ...env },
        stdout: text => output.push(text), stderr: text => errors.push(text) });
      return { code, requests, result: output.length ? JSON.parse(output.join('\n')) : null, errors };
    } finally { process.chdir(originalCwd); }
  };
  const records = async () => (await readFile(join(root, '.perch/scan.jsonl'), 'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);
  return { root, configure, commit, run, records };
}

test('incremental scans reuse exact answers and parser blobs across commits, including dependent contexts', async t => {
  const f = await fixture(t);
  const cold = await f.run();
  assert.equal(cold.code, 0, cold.errors.join('\n'));
  assert.equal(cold.requests.length, 3);
  assert.equal(cold.result.run.mode, 'incremental');
  assert.equal(cold.result.parser_coverage.parser_cache.misses, 3);
  assert.ok(cold.result.run.reviewed_checks > 0);
  assert.equal(cold.result.run.reviewed_checks, cold.result.run.coverage.reduce((sum, row) => sum + row.units, 0));
  assert.equal(cold.result.run.coverage.find(row => row.name === 'fixture').units, 3);
  const warm = await f.run();
  assert.equal(warm.requests.length, 0);
  assert.equal(warm.result.run.carried, 3);
  assert.equal(warm.result.run.reviewed_checks, cold.result.run.reviewed_checks);
  assert.deepEqual(warm.result.run.coverage, cold.result.run.coverage);
  assert.deepEqual(warm.result.parser_coverage.parser_cache, { hits: 0, misses: 0, write_failures: 0, revision_reused: true });
  await writeFile(join(f.root, 'note.md'), 'Unrelated documentation.\n'); f.commit();
  const docs = await f.run();
  assert.equal(docs.requests.length, 0);
  assert.deepEqual(docs.result.parser_coverage.parser_cache, { hits: 3, misses: 0, write_failures: 0, revision_reused: false });
  await writeFile(join(f.root, 'src/helper.bend'), 'import Base\ndef value(x: U32) -> U32: U32.add(x, 2)\n'); f.commit();
  const changed = await f.run();
  assert.equal(changed.code, 0, changed.errors.join('\n'));
  assert.deepEqual(changed.requests.map(r => r.state.method.path).sort(), ['src/helper.bend', 'src/main.bend']);
  assert.equal(changed.result.run.carried, 1);
  assert.equal(changed.result.parser_coverage.parser_cache.hits, 2);
  assert.equal(changed.result.parser_coverage.parser_cache.misses, 1);
  const fresh = await f.run({ args: ['--fresh'] });
  assert.equal(fresh.requests.length, 3);
  assert.equal(fresh.result.run.carried, 0);
  assert.equal(fresh.result.run.mode, 'fresh');
  assert.equal((await f.run()).requests.length, 0);
  for (const env of [{ PERCH_MODEL_ID: 'another-model' }, { PERCH_BASE_URL: 'https://offline.invalid/custom' }]) {
    assert.equal((await f.run({ env })).requests.length, 3, 'model and endpoint changes invalidate prior answers');
  }
  for (const args of [['--incremental', '--fresh'], ['--incremental', '--since', 'HEAD'], ['--fresh', '--since', 'HEAD']]) {
    const invalid = await f.run({ args });
    assert.equal(invalid.code, 2); assert.equal(invalid.requests.length, 0);
  }
});

test('renamed method rules cannot carry an answer under the old question name', async t => {
  const f = await fixture(t, [methodRule('fixture-old')]);
  const failing = body => {
    const response = answer(body);
    for (const name of Object.keys(body.questions)) if (name.startsWith('fixture')) response.answers[name] = { noul: 0 };
    return response;
  };
  assert.equal((await f.run({ respond: failing })).code, 3);
  await f.configure([methodRule('fixture-new')]);
  const changed = await f.run({ respond: failing });
  assert.equal(changed.requests.length, 3);
  assert.equal(changed.code, 3);
  assert.deepEqual(new Set(changed.result.run.broken.map(item => item.rule)), new Set(['fixture-new']));
  const warm = await f.run({ respond: failing });
  assert.equal(warm.requests.length, 0); assert.equal(warm.code, 3);
});

test('renamed and deleted files, and failed dependent rereads, do not retain stale successful units', async t => {
  const f = await fixture(t, [methodRule('fixture'), { name: 'fixture-file', where: 'docs/**/*.md', each: 'file', ensure: 'A valid packet.' }]);
  await mkdir(join(f.root, 'docs')); await writeFile(join(f.root, 'docs/packet.md'), 'One packet.\n'); f.commit();
  assert.equal((await f.run()).requests.length, 4);
  await rename(join(f.root, 'docs/packet.md'), join(f.root, 'docs/renamed.md')); f.commit();
  const renamed = await f.run();
  assert.equal(renamed.requests.length, 1);
  assert.deepEqual((await f.records()).filter(r => r.rule).map(r => r.unit), ['docs/renamed.md']);
  await rm(join(f.root, 'docs/renamed.md')); f.commit();
  assert.equal((await f.run()).requests.length, 0);
  assert.equal((await f.records()).filter(r => r.rule).length, 0);
  await writeFile(join(f.root, 'src/helper.bend'), 'import Base\ndef value(x: U32) -> U32: U32.add(x, 3)\n'); f.commit();
  const failed = await f.run({ respond: body => body.state.method?.path === 'src/main.bend'
    ? { model: 'offline-incremental', answers: {} } : answer(body) });
  assert.equal(failed.result.run.failed.length, 1);
  assert.equal(failed.result.run.coverage.find(row => row.name === 'fixture').units, 2);
  assert.equal(failed.result.run.reviewed_checks, failed.result.run.coverage.reduce((sum, row) => sum + row.units, 0));
  assert.ok(!(await f.records()).some(r => r.method === 'src/main.bend::main'), 'a failed new context must not expose the prior answer as current');
  await rm(join(f.root, 'src/helper.bend')); f.commit();
  const deleted = await f.run();
  assert.equal(deleted.code, 0, deleted.errors.join('\n'));
  assert.ok(!(await f.records()).some(r => r.path === 'src/helper.bend'));
});

test('search reuse includes actual helper context, rule kind, threshold and an empty selection', async t => {
  const search = kind => ({ name: 'fixture-search', where: 'src/main.bend', each: 'method', [kind]: 'The requested behavior exists.' });
  const f = await fixture(t, [methodRule('fixture'), search('ensure_present')]);
  const initial = await f.run();
  assert.equal(initial.code, 0, initial.errors.join('\n'));
  assert.equal((await f.run()).requests.length, 0);
  await writeFile(join(f.root, 'src/helper.bend'), 'import Base\ndef value(x: U32) -> U32: U32.add(x, 4)\n'); f.commit();
  const changed = await f.run();
  assert.ok(changed.requests.some(r => 'fixture-search' in r.questions), 'a Bend self search includes its helper context');
  await f.configure([methodRule('fixture'), search('ensure_absent')]);
  const absent = await f.run();
  assert.equal(absent.code, 3);
  assert.ok(absent.requests.some(r => 'fixture-search' in r.questions));
  const stricter = await f.run({ args: ['--incremental', '--min', '100'] });
  assert.ok(stricter.requests.some(r => 'fixture-search' in r.questions));
  assert.equal(stricter.result.run.broken.length, 0);
  await rm(join(f.root, 'src/main.bend')); f.commit();
  await f.configure([methodRule('fixture'), search('ensure_present')]);
  const empty = await f.run();
  assert.equal(empty.code, 3);
  const event = (await f.records()).find(r => r.rule === 'fixture-search');
  assert.equal(event.broken, 1, 'an empty existential search has a deterministic missing result');
});

test('parser cache corruption is a miss; transient failures never become persistent cache entries', async t => {
  const f = await fixture(t);
  await f.run();
  const cacheDir = join(f.root, '.perch/analysis');
  const names = await readdir(cacheDir);
  assert.equal(names.length, 3);
  await writeFile(join(cacheDir, names[0]), '{broken');
  await writeFile(join(f.root, 'note.md'), 'Next revision.\n'); f.commit();
  const repaired = await f.run();
  assert.equal(repaired.requests.length, 0);
  assert.equal(repaired.result.parser_coverage.parser_cache.hits, 2);
  assert.equal(repaired.result.parser_coverage.parser_cache.misses, 1);
  let attempts = 0;
  const analyzer = { async analyzeSource() { return { parser_status: ++attempts === 1 ? 'resource-unavailable' : 'parsed', declarations: [], references: [], diagnostics: [] }; } };
  const stats = () => ({ hits: 0, misses: 0, write_failures: 0 });
  assert.equal((await knotCachedAnalyzer(analyzer, f.root, stats()).analyzeSource('fixture source', 'bend')).parser_status, 'resource-unavailable');
  assert.equal((await knotCachedAnalyzer(analyzer, f.root, stats()).analyzeSource('fixture source', 'bend')).parser_status, 'parsed');
  const cached = stats(); await knotCachedAnalyzer(analyzer, f.root, cached).analyzeSource('fixture source', 'bend');
  assert.equal(attempts, 2); assert.equal(cached.hits, 1);
});
