#!/usr/bin/env node
// Whole-repository plumbing profile. Fixed offline answers are not review evidence.
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { DEFAULT_PERCH_JOBS, perchConcurrency } from './perch-throughput.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
process.chdir(root);
const args = process.argv.slice(2);
const option = (name, fallback) => args.find(arg => arg.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback;
if (args.some(arg => arg !== '--live' && !['--kind=', '--jobs=', '--output=', '--module=', '--env-file='].some(prefix => arg.startsWith(prefix)))) {
  throw new Error('Use --kind=scan|style --jobs=N --output=new.json [--live --env-file=path --module=baseline.mjs]');
}
const kind = option('kind', 'scan'), live = args.includes('--live');
if (!['scan', 'style'].includes(kind)) throw new Error('Profile kind must be scan or style');
const jobs = perchConcurrency(option('jobs', DEFAULT_PERCH_JOBS));
const output = option('output', null);
if (!output) throw new Error('Supply a new output JSON path');
await mkdir(dirname(resolve(output)), { recursive: true });
await writeFile(resolve(output), '', { flag: 'wx', mode: 0o600 });
if (live && option('env-file', null)) process.loadEnvFile(resolve(option('env-file')));
const env = live ? Object.fromEntries(['PERCH_API_KEY', 'TYPESAFE_API_KEY', 'PERCH_BASE_URL', 'PERCH_MODEL_ID']
  .filter(key => process.env[key]).map(key => [key, process.env[key]]))
  : { PERCH_API_KEY: 'offline-throughput-probe', PERCH_MODEL_ID: 'offline-throughput-probe' };
if (live && !env.PERCH_API_KEY && !env.TYPESAFE_API_KEY) throw new Error('Live profiling requires a configured Perch key');
const modulePath = resolve(root, option('module', kind === 'scan' ? 'node_modules/@lakeday/perch/dist/cli.mjs' : 'scripts/perch-style.mjs'));
const command = await import(pathToFileURL(modulePath));
const sha = value => createHash('sha256').update(value).digest('hex');
const originalFetch = globalThis.fetch, requests = [];
let active = 0, peak = 0, result, diagnostics = 0;
const started = performance.now();
function fixedAnswer(name, question) {
  if (question.type === 'noul') return { noul: name.includes('-') || name === 'does_what_it_claims' ? 1 : 0 };
  if (question.type === 'choice') {
    const choice = Object.keys(question.criteria).at(-1);
    return { choice, confidence: 1, probabilities: { [choice]: 1 } };
  }
  if (question.type === 'score') {
    const score = question.criteria.length - 1;
    return { type: 'score', score, confidence: 1,
      probabilities: Object.fromEntries(question.criteria.map((_, index) => [index, Number(index === score)])) };
  }
  throw new Error(`Unknown offline question type: ${question.type}`);
}
const fetchImpl = async (url, init) => {
  const body = JSON.parse(init.body);
  const row = { request_sha256: sha(init.body), state_sha256: sha(JSON.stringify(body.state)),
    question_ids: Object.keys(body.questions).sort(), start_ms: performance.now() - started };
  requests.push(row); peak = Math.max(peak, ++active);
  try {
    const response = live ? await originalFetch(url, init) : new Response(JSON.stringify({
      model: env.PERCH_MODEL_ID,
      answers: Object.fromEntries(Object.entries(body.questions).map(([name, question]) => [name, fixedAnswer(name, question)])),
    }));
    row.status = response.status;
    if (response.ok) row.model = (await response.clone().json()).model;
    if (response.status === 429) row.retry_after = response.headers.get('retry-after');
    return response;
  } finally { row.elapsed_ms = performance.now() - started - row.start_ms; active--; }
};
let code, failure;
try {
  if (kind === 'scan') {
    globalThis.fetch = fetchImpl;
    code = await command.main(['scan', '--parallel', String(jobs), '--out',
      resolve(root, '.perch/throughput-profiles', randomUUID()), '--json'], {
      env, stdout: text => { result = JSON.parse(text); }, stderr: () => { diagnostics++; },
    });
  } else {
    code = await command.runStyleRanking(['--live', '--all', '--json', `--jobs=${jobs}`], {
      root, env, fetchImpl, stdout: text => { result = JSON.parse(text); }, stderr: () => { diagnostics++; },
    });
  }
} catch (error) { code = 1; failure = error.name; }
finally { globalThis.fetch = originalFetch; }
const wall_ms = performance.now() - started;
const report = {
  schema: 1, at: new Date().toISOString(), kind, live, jobs, code, failure, wall_ms, peak, diagnostics,
  revision: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
  node: process.version, module_sha256: sha(await readFile(modulePath)),
  rubric_sha256: kind === 'style' ? sha(await readFile(resolve(root, 'perch-style.json'))) : undefined,
  requests: requests.length, request_set_sha256: sha(JSON.stringify(requests.map(row => row.request_sha256).sort())),
  responses_by_status: Object.fromEntries([...new Set(requests.map(row => row.status))].map(status => [status, requests.filter(row => row.status === status).length])),
  coverage: kind === 'style' ? result?.coverage : {
    methods: result?.run?.methods, failed: result?.run?.failed?.length, carried: result?.run?.carried,
    supported: result?.parser_coverage?.supported, parsed: result?.parser_coverage?.parsed,
    parse_failures: result?.parser_coverage?.parse_failures,
  },
  timings: result?.timings, request_timings: requests,
  note: 'Imported command wall time includes preflight and receipt writes, excludes module imports. Fresh scan store prevents answer reuse. Fixed offline answers measure plumbing only. Native scan exit code does not enforce the project wrapper parser-coverage gate. Requests retain hashes/timing only; no source bodies, credentials or response error text.',
};
await writeFile(resolve(output), JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
console.log(JSON.stringify({ ...report, request_timings: undefined }));
