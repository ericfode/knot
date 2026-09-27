#!/usr/bin/env node
// Measure the installed check/style paths without changing their scheduling.
// Offline timings use fixed answers and are never semantic/style evidence.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { runPerch } from './perch-workflow.mjs';
import { runStyleRanking } from './perch-style.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const known = arg => arg === '--live' || ['--env-file=', '--output=', '--target=', '--unit='].some(prefix => arg.startsWith(prefix));
if (args.some(arg => !known(arg))) throw new Error('Use --target=file.bend --unit=name --output=new.json [--live --env-file=path]');
const option = (name, fallback) => args.find(arg => arg.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
const target = option('target', 'packages/source/main.bend');
const unit = option('unit', 'locate');
const output = option('output', null);
const live = args.includes('--live');
if (output) {
  // Refuse overwriting evidence before performing any paid work.
  await mkdir(dirname(resolve(output)), { recursive: true });
  await writeFile(resolve(output), '', { flag: 'wx', mode: 0o600 });
}
if (live && option('env-file', null)) process.loadEnvFile(resolve(option('env-file')));
const liveEnv = Object.fromEntries(['PERCH_API_KEY', 'TYPESAFE_API_KEY', 'PERCH_BASE_URL', 'PERCH_MODEL_ID']
  .filter(key => process.env[key]).map(key => [key, process.env[key]]));
if (live && !liveEnv.PERCH_API_KEY && !liveEnv.TYPESAFE_API_KEY) throw new Error('Live profiling requires a configured Perch key');
const offlineEnv = { PERCH_API_KEY: 'offline-latency-probe', PERCH_MODEL_ID: 'offline-latency-probe' };
const rules = ['perf-growing-prefix-copy', 'perf-loop-invariant-work', 'perf-linked-list-indexing', 'perf-amortized-growth'];
const round = number => Math.round(number * 100) / 100;
const sha = value => createHash('sha256').update(value).digest('hex');
const summary = numbers => {
  const sorted = [...numbers].sort((a, b) => a - b);
  return { count: sorted.length, sum: round(sorted.reduce((a, b) => a + b, 0)),
    median: sorted.length ? round((sorted[Math.floor((sorted.length - 1) / 2)] + sorted[Math.floor(sorted.length / 2)]) / 2) : null,
    p95: sorted.length ? round(sorted[Math.ceil(sorted.length * .95) - 1]) : null,
    max: sorted.length ? round(sorted.at(-1)) : null };
};
const nativeFetch = globalThis.fetch;
const report = {
  schema: 1, at: new Date().toISOString(), revision: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  node: process.version, target, unit, rules,
  source_sha256: sha(await readFile(resolve(root, target))),
  script_sha256: sha(await readFile(fileURLToPath(import.meta.url))),
  live, runs: [],
  note: 'Client round trips include network, provider processing and response decoding; they do not isolate model inference. Offline fixed answers measure plumbing only. Run wall time excludes module imports but includes preflight and receipt writes. Original check/style receipts remain in ignored .perch/usage. Repeated live inputs may benefit from provider caching.',
};
const importStart = performance.now();
await import('../node_modules/@lakeday/perch/dist/cli.mjs');
report.perch_cli_import_ms = round(performance.now() - importStart);

function fixedAnswer(question) {
  if (question.type === 'noul') return { noul: 1 };
  if (question.type === 'score') {
    const levels = question.criteria.length;
    return { type: 'score', score: levels - 1, confidence: 1,
      probabilities: Object.fromEntries(Array.from({ length: levels }, (_, i) => [i, i === levels - 1 ? 1 : 0])) };
  }
  throw new Error(`Unsupported offline question type: ${question.type}`);
}

async function measure({ kind, mode, selected = target, jobs = 1, delayMs = 0 }) {
  let active = 0, peak = 0, result;
  const requests = [], errorClasses = [];
  const start = performance.now();
  const fetchImpl = async (url, init) => {
    const body = JSON.parse(init.body);
    const request = { start_ms: round(performance.now() - start), questions: Object.keys(body.questions).length,
      request_bytes: Buffer.byteLength(init.body), state_sha256: sha(JSON.stringify(body.state)) };
    requests.push(request);
    peak = Math.max(peak, ++active);
    const sent = performance.now();
    try {
      let response;
      if (mode === 'live') response = await nativeFetch(url, init);
      else {
        if (delayMs) await delay(delayMs);
        response = new Response(JSON.stringify({ model: 'offline-latency-probe', answers:
          Object.fromEntries(Object.entries(body.questions).map(([name, question]) => [name, fixedAnswer(question)])) }));
      }
      request.headers_ms = round(performance.now() - sent);
      request.http_status = response.status;
      // Never retain request text, headers, credentials or provider errors.
      if (response.ok) {
        const answer = await response.clone().json();
        request.model = answer.model;
      }
      return response;
    } catch (error) {
      request.error_class = error.name;
      throw error;
    } finally {
      request.round_trip_ms = round(performance.now() - sent);
      request.end_ms = round(performance.now() - start);
      active--;
    }
  };
  const env = mode === 'live' ? liveEnv : offlineEnv;
  const stdout = text => { result = JSON.parse(text); };
  const stderr = () => { errorClasses.push('command-diagnostic'); };
  let exit;
  try {
    if (kind === 'check') {
      globalThis.fetch = fetchImpl;
      exit = await runPerch(['check', selected, '--rules', rules.join(',')], { root, env, stdout, stderr });
    } else {
      exit = await runStyleRanking(['--live', '--json', selected, `--jobs=${jobs}`], { root, env, fetchImpl, stdout, stderr });
    }
  } finally { globalThis.fetch = nativeFetch; }
  const wall = performance.now() - start;
  let until = 0, occupied = 0;
  for (const request of [...requests].sort((a, b) => a.start_ms - b.start_ms)) {
    occupied += Math.max(0, request.end_ms - Math.max(until, request.start_ms));
    until = Math.max(until, request.end_ms);
  }
  const row = { kind, mode, target: selected, jobs: kind === 'style' ? jobs : null, injected_delay_ms: delayMs,
    exit, wall_ms: round(wall), checked: result?.checked ?? null,
    units: kind === 'style' ? result?.coverage?.ranked : result?.units?.length ?? (result?.context ? 1 : 0),
    peak_inflight: peak, round_trip_ms: summary(requests.map(r => r.round_trip_ms)),
    request_bytes: summary(requests.map(r => r.request_bytes)),
    outside_fetch_ms: round(wall - occupied),
    style_receipt_elapsed_ms: kind === 'style' ? result?.elapsed_ms : null,
    diagnostic_count: errorClasses.length, requests };
  report.runs.push(row);
  if (output) await writeFile(resolve(output), JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
  console.log(JSON.stringify({ ...row, requests: requests.length }));
  assert.ok(exit === 0 || exit === 3, `${kind}/${mode} did not complete; see retained receipt`);
  assert.ok(requests.length > 0, 'Profiling requires nonzero provider coverage');
  return row;
}

await measure({ kind: 'check', mode: 'offline', selected: `${target}::${unit}` });
const local = await measure({ kind: 'check', mode: 'offline' });
const delayed = await measure({ kind: 'check', mode: 'offline', delayMs: 25 });
assert.equal(local.units, delayed.units);
assert.equal(local.requests.length, delayed.requests.length);
assert.equal(delayed.peak_inflight, 1, 'Revisit the serial-dispatch diagnosis if the implementation changes');
const serial = await measure({ kind: 'style', mode: 'offline', jobs: 1, delayMs: 25 });
const parallel = await measure({ kind: 'style', mode: 'offline', jobs: 8, delayMs: 25 });
assert.deepEqual(serial.requests.map(r => r.state_sha256).sort(), parallel.requests.map(r => r.state_sha256).sort(), 'Compare identical review states');
assert.equal(serial.peak_inflight, 1);
assert.equal(parallel.peak_inflight, Math.min(8, serial.requests.length));
if (live) {
  await measure({ kind: 'check', mode: 'live' });
  await measure({ kind: 'style', mode: 'live', jobs: 1 });
  await measure({ kind: 'style', mode: 'live', jobs: 8 });
}
