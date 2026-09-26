import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { prepareStyleTargets, rankRows, runStyleRanking, validateScore } from '../scripts/perch-style.mjs';

const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
const targets = ['a.bend::solve', 'b.bend::solve'];
const args = ['--live', '--json', '--cohort=Add one to an unsigned word', ...targets];
const key = 'offline-secret-must-not-be-recorded';
const source = 'import Base\nimport ./helper.bend as H\ndef solve(x: U32) -> U32: H.next(x)\ndef unrelated() -> U32: 999\n';
const score = level => ({ type: 'score', score: level, confidence: 1,
  probabilities: Object.fromEntries(config.dimensions[0].levels.map((_, i) => [i, i === level ? 1 : 0])) });
const response = (brain = 3, delight = 2, model = 'offline-style-fixture') => ({ ok: true, json: async () => ({
  model, answers: { maximally_big_brain: score(brain), delightful_to_read: score(delight) },
  usage: { input_tokens: 100, output_tokens: 10 },
}) });

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-style-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  await writeFile(join(root, 'a.bend'), source);
  await writeFile(join(root, 'b.bend'), 'import Base\ndef solve(x: U32) -> U32: U32.add(x,1)\n');
  await writeFile(join(root, 'helper.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,1)\n');
  return root;
}

test('rank preflight uses exact parsed units and working-copy helpers; all inputs validate before paid calls', async t => {
  const root = await fixture(t);
  const units = await prepareStyleTargets([...targets, targets[0]], 'Add one', config, root);
  assert.equal(units.length, 2, 'duplicate selections must not cause paid repeats');
  assert.match(units[0].state.source, /^def solve/);
  assert.ok(!units[0].state.source.includes('unrelated'));
  assert.equal(units[0].state.calls[0].name, 'next');
  assert.deepEqual(units[0].context.files.map(f => f.path), ['a.bend', 'helper.bend']);
  let calls = 0;
  const run = selection => runStyleRanking(['--live', '--cohort=Add one', ...selection], {
    root, env: { PERCH_API_KEY: key }, fetchImpl: async () => { calls++; return response(); },
  });
  await assert.rejects(run([targets[0]]), /at least two/);
  await assert.rejects(run([...targets, 'b.bend::missing']), /No applicable parsed declaration/);
  await assert.rejects(prepareStyleTargets(['a.bend', 'b.bend'], 'Add one', { ...config, max_units: 2 }, root), /limited to 2/);
  await writeFile(join(root, 'b.bend'), 'def broken( -> U32: 0\n');
  await assert.rejects(run(targets), /does not parse/);
  assert.equal(calls, 0);
  await writeFile(join(root, 'helper.bend'), 'def next( -> U32: 0\n');
  await assert.rejects(run(targets), /context .*does not parse/);
  assert.equal(calls, 0);
});

test('one request per unit carries two ordinal questions; receipts rank each axis without source or secrets', async t => {
  const root = await fixture(t), requests = [], output = [];
  const code = await runStyleRanking(args, { root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x),
    fetchImpl: async (_url, request) => {
      requests.push(JSON.parse(request.body));
      assert.equal(request.headers.authorization, `Bearer ${key}`);
      return requests.length === 1 ? response(4, 1) : response(2, 4);
    },
  });
  assert.equal(code, 0);
  assert.equal(requests.length, 2);
  for (const request of requests) {
    assert.equal(Object.keys(request.questions).length, 2);
    assert.ok(Object.values(request.questions).every(q => q.type === 'score' && q.criteria.length === 5));
  }
  const report = JSON.parse(output[0]);
  assert.equal(report.status, 'completed');
  assert.equal(report.provider_requests, 2);
  assert.equal(report.provider_responses, 2);
  assert.equal(report.rankings[0].entries[0].target, targets[0]);
  assert.equal(report.rankings[1].entries[0].target, targets[1]);
  assert.equal(report.typechecked, false);
  assert.equal(report.behavioral_equivalence_checked, false);
  const receipts = await readdir(join(root, '.perch/usage'));
  assert.equal(receipts.length, 1);
  const saved = await readFile(join(root, '.perch/usage', receipts[0]), 'utf8');
  assert.deepEqual(JSON.parse(saved), report);
  assert.ok(!saved.includes(key) && !saved.includes('def solve') && !saved.includes('def next'));
});

test('partial transport failure records incomplete coverage, stops requests, and never returns a partial ranking', async t => {
  const root = await fixture(t), output = [], errors = [];
  let calls = 0;
  const code = await runStyleRanking([...args, 'a.bend::unrelated'], {
    root, env: { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: x => errors.push(x),
    fetchImpl: async () => {
      if (++calls === 2) throw new Error(`unsafe request details ${key}`);
      return response();
    },
  });
  assert.equal(code, 1);
  assert.equal(calls, 2);
  const report = JSON.parse(output[0]);
  assert.equal(report.status, 'failed');
  assert.equal(report.provider_requests, 2);
  assert.equal(report.provider_responses, 1);
  assert.deepEqual(report.rows, []);
  assert.deepEqual(report.rankings, []);
  assert.ok(!JSON.stringify([report, errors]).includes(key));
});

test('missing credentials, unauthorized responses, malformed scores and model drift cannot produce rankings', async t => {
  const root = await fixture(t);
  const invalid = response();
  invalid.json = async () => ({ model: 'offline', answers: { maximally_big_brain: score(4) } });
  for (const mode of ['missing-key', 'unauthorized', 'invalid-answer', 'model-drift']) {
    let calls = 0;
    const output = [];
    const code = await runStyleRanking(args, {
      root, env: mode === 'missing-key' ? {} : { PERCH_API_KEY: key }, stdout: x => output.push(x), stderr: () => {},
      fetchImpl: async () => {
        calls++;
        if (mode === 'unauthorized') return { ok: false, status: 401 };
        if (mode === 'invalid-answer') return invalid;
        return response(3, 2, `offline-${calls}`);
      },
    });
    const report = JSON.parse(output[0]);
    assert.equal(code, 1, mode);
    assert.equal(report.status, 'failed', mode);
    assert.deepEqual(report.rankings, [], mode);
    assert.equal(calls, mode === 'missing-key' ? 0 : mode === 'model-drift' ? 2 : 1, mode);
  }
  assert.throws(() => validateScore({ ...score(4), score: 1 }, 5), /Inconsistent/);
  assert.throws(() => validateScore({ ...score(4), probabilities: { 4: 1 } }, 5), /Incomplete/);
});

test('ties share a rank, near ties remain visible, and existing output is rejected before requests', async t => {
  const root = await fixture(t);
  const rows = [4, 4, 3.8, 2].map((value, i) => ({ target: String(i), answers: { taste: { score: value } } }));
  const ranked = rankRows(rows, [{ id: 'taste' }], 0.25)[0].entries;
  assert.deepEqual(ranked.map(row => row.rank), [1, 1, 3, 4]);
  assert.deepEqual(ranked.map(row => row.near_tie_above), [false, true, true, false]);
  await writeFile(join(root, 'old.json'), 'old evidence');
  let calls = 0;
  await assert.rejects(runStyleRanking([...args, '--output=old.json'], { root,
    fetchImpl: async () => { calls++; return response(); },
  }), /already exists/);
  assert.equal(calls, 0);
  assert.equal(await readFile(join(root, 'old.json'), 'utf8'), 'old evidence');
});
