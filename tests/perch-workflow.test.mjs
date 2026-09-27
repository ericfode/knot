import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { runPerch, usageSummary } from '../scripts/perch-workflow.mjs';

test('actual Perch CLI retains useful evidence without treating blockers or zero coverage as passes', async () => {
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-workflow-'));
  const originalFetch = globalThis.fetch;
  let calls = 0, verdict = 1, denied = false;
  const secret = 'fixture-credential-never-write-to-receipts';
  try {
    await mkdir(join(root, 'src'));
    await writeFile(join(root, 'src/probe.bend'), 'import Base\n\ndef main() -> U32:\n  42\n');
    await writeFile(join(root, 'note.md'), '# No applicable rules\n');
    await writeFile(join(root, 'perch.yaml'), 'rules:\n  - name: probe\n    where: "**/*.bend"\n    each: file\n    min: 80\n    gate: false\n    ensure: This is a wiring fixture.\n');
    const git = args => execFileSync('git', args, { cwd: root, stdio: 'ignore' });
    git(['init', '-q', '-b', 'main']);
    git(['add', '.']);
    git(['-c', 'user.name=Workflow test', '-c', 'user.email=fixture@example.invalid',
      '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Fixture']);
    globalThis.fetch = async (_url, options) => {
      calls++;
      if (denied) return { ok: false, status: 401, text: async () => secret };
      const body = JSON.parse(options.body);
      const reply = { model: 'offline-fixture', usage: { input_tokens: 100, output_tokens: 10 }, answers:
        Object.fromEntries(Object.keys(body.questions).map(name => [name, { noul: verdict }])) };
      return { ok: true, json: async () => reply, clone: () => ({ json: async () => reply }) };
    };
    const run = (args, env = { PERCH_API_KEY: secret }) => runPerch(args, {
      root, env, stdout: () => {}, stderr: () => {},
    });
    const check = ['check', 'src/probe.bend', '--rules', 'probe'];
    assert.equal(await run(check), 0);
    assert.equal(calls, 1);
    verdict = 0;
    assert.equal(await run(check), 3);
    assert.equal(calls, 2);
    assert.equal(await run(['check', 'note.md', '--rules', 'probe']), 1);
    assert.equal(calls, 2, 'zero coverage does not contact the provider');
    assert.equal(await run(check, {}), 1);
    assert.equal(calls, 2, 'missing credentials do not contact the provider');
    denied = true;
    assert.equal(await run(check), 1);
    assert.equal(calls, 3, 'authorization failure does not retry');
    assert.equal(await run(['scan', '--since', 'HEAD']), 0);
    assert.equal(calls, 3, 'an unchanged scan does not contact the provider');
    const names = await readdir(join(root, '.perch/usage'));
    assert.equal(names.length, 6);
    const raw = await Promise.all(names.map(name => readFile(join(root, '.perch/usage', name), 'utf8')));
    assert.ok(raw.every(text => !text.includes(secret)));
    assert.ok(raw.every(text => !text.includes('def main()')));
    const records = raw.map(JSON.parse);
    assert.deepEqual(records.map(r => r.status).sort(), ['completed', 'failed', 'findings', 'missing-key', 'no-coverage', 'unchanged']);
    const reported = records.find(r => r.status === 'findings');
    assert.equal(reported.checked, 1);
    assert.equal(reported.findings[0].rule, 'probe');
    assert.equal(reported.findings[0].probability, 1);
    assert.equal(reported.source_sha256.length, 64);
    assert.equal(reported.rules_sha256.length, 64);
    assert.deepEqual(reported.selected_rules, ['probe']);
    assert.equal(reported.resolved_model, 'offline-fixture');
    assert.equal(reported.provider_requests, 1);
    assert.equal(reported.answers[0].probability_true, 0);
    assert.equal(reported.usage.input_tokens, 100);
    const summary = await usageSummary(root);
    assert.equal(summary.receipts, 6);
    assert.equal(summary.statuses['missing-key'], 1);
    assert.equal(summary.findings.probe, 1);
    assert.equal(summary.malformed, 0);
    denied = false;
    verdict = 'not-a-probability';
    assert.equal(await run(check), 1, 'a malformed noul must not become a clean result');
  } finally {
    globalThis.fetch = originalFetch;
    await rm(root, { recursive: true, force: true });
  }
});

test('bounded workers refill, preserve order and drain when a task fails', async () => {
  const { mapConcurrent } = await import('../scripts/perch-throughput.mjs');
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  const started = [];
  const job = mapConcurrent([0,1,2,3,4], 2, async i => {
    started.push(i);
    if (i === 0) await gate;
    if (i === 4) release();
    return i * 2;
  });
  assert.deepEqual(await job, [0,2,4,6,8]);
  assert.deepEqual(started, [0,1,2,3,4], 'later work refills behind a slow first task');
  let finished = false;
  await assert.rejects(mapConcurrent([0,1,2,3], 2, async i => {
    if (i === 0) { await new Promise(resolve => setTimeout(resolve, 5)); finished = true; }
    if (i === 1) throw new Error('fixture failure');
    assert.ok(i < 2, 'no new work after failure');
  }), /fixture failure/);
  assert.ok(finished, 'in-flight work drains before rejection');
});

test('token memoization is exact under mutation, Unicode and bounded eviction', async () => {
  const { memoizeTextCount } = await import('../scripts/perch-throughput.mjs');
  let calls = 0;
  const count = text => { calls++; return Buffer.byteLength(text); };
  const cached = memoizeTextCount(count, { characters: 20, entries: 2 });
  for (const text of ['😀', 'é', '😀']) assert.equal(cached(text), Buffer.byteLength(text));
  assert.equal(calls, 2);
  const state = {x:1}; const first = cached(JSON.stringify(state));
  state.reading = true;
  assert.notEqual(cached(JSON.stringify(state)), first, 'mutated request metadata gets a fresh count');
  assert.equal(cached('x'.repeat(30)), 30); assert.equal(cached('x'.repeat(30)), 30);
  const before = calls; cached('a'); cached('b'); cached('c'); cached('a');
  assert.equal(calls - before, 4, 'evicted strings are recomputed');
});

test('provider semaphore bounds nested fan-out and drains arbitrary rejections', async () => {
  const { drainAll, limitConcurrent, mapConcurrent, failureCohorts } = await import('../scripts/perch-throughput.mjs');
  let active = 0, peak = 0, completed = 0;
  const request = limitConcurrent(async i => {
    peak = Math.max(peak, ++active);
    await new Promise(resolve => setTimeout(resolve, 1));
    active--; completed++;
    if (i === 3) throw 0;
    return i;
  }, 3);
  let rejection = Symbol('unset');
  try { await drainAll(Array.from({ length: 12 }, (_, i) => request(i))); }
  catch (error) { rejection = error; }
  assert.equal(rejection, 0); assert.equal(peak, 3); assert.equal(active, 0); assert.equal(completed, 12);
  let started = 0;
  try { await mapConcurrent([0,1,2], 1, async () => { started++; throw undefined; }); }
  catch (error) { assert.equal(error, undefined); }
  assert.equal(started, 1, 'falsy rejection still stops admission');
  const failure = failureCohorts(2);
  for (const i of [1,2,3,4]) assert.equal(failure(i, true), false, 'wait for the slow earlier completion');
  assert.equal(failure(0, false), false, 'its success prevents the first cohort from counting as failed');
  assert.equal(failure(5, true), true, 'two following fully failed cohorts stop the scan');
});

test('scan checkpoint accounts only for serialized rows when workers finish during append', async t => {
  const fs = (await import('node:fs/promises')).default;
  const { syncBuiltinESMExports } = await import('node:module');
  const { knotOpenStore } = await import('../node_modules/@lakeday/perch/dist/cli.mjs');
  const root = await mkdtemp(join(tmpdir(), 'knot-perch-journal-'));
  const original = fs.appendFile;
  t.after(async () => { fs.appendFile = original; syncBuiltinESMExports(); await rm(root, {recursive:true,force:true}); });
  const store = knotOpenStore(root);
  const run = {id:'fixture',status:'running',calls:0,carried:0,usage:{input_tokens:0,output_tokens:0},visited:[],broken:[],failed:[]};
  const save = await store.startRun(run);
  let enter, release;
  const entered = new Promise(resolve => { enter = resolve; });
  const gate = new Promise(resolve => { release = resolve; });
  fs.appendFile = async (...args) => { enter(); await gate; return original(...args); };
  syncBuiltinESMExports();
  run.visited.push({id:'first'});run.calls=1;run.usage.input_tokens=10;
  const saving = save(); await entered;
  run.visited.push({id:'second'});run.calls=2;run.usage.input_tokens=20;
  release(); await saving;
  const path = join(store.runDir(run.id),'run.json');
  const checkpoint = JSON.parse(await readFile(path,'utf8'));
  assert.equal(checkpoint.calls,1);assert.equal(checkpoint.usage.input_tokens,10);
  fs.appendFile=original;syncBuiltinESMExports();
  await save();
  const rows=(await readFile(join(store.runDir(run.id),'progress.jsonl'),'utf8')).trim().split('\n').flatMap(line=>JSON.parse(line).visited);
  assert.deepEqual(rows,[{id:'first'},{id:'second'}]);
  await save(true);
  const final=JSON.parse(await readFile(path,'utf8'));assert.equal(final.calls,2);assert.deepEqual(final.visited,rows);
});
