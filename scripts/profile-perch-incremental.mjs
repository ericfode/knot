#!/usr/bin/env node
// Reproducible full-repository cache exercise. Fixed answers are not model review.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPerch } from './perch-workflow.mjs';
import { runStyleRanking } from './perch-style.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
if (args.length !== 1 || !args[0].startsWith('--output=')) {
  throw new Error('Use --output=new.json; this profile never contacts a provider');
}
const output = resolve(args[0].slice('--output='.length));
await mkdir(dirname(output), { recursive: true });
await writeFile(output, '', { flag: 'wx', mode: 0o600 });
const fixture = await mkdtemp(join(tmpdir(), 'knot-perch-incremental-profile-'));
const sha = value => createHash('sha256').update(value).digest('hex');
const git = (...args) => execFileSync('git', args, { cwd: fixture, encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
const commit = message => git('-c', 'user.name=Perch profile', '-c', 'user.email=fixture@example.invalid',
  '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', message);
const env = { PERCH_API_KEY: 'offline-incremental-profile', PERCH_MODEL_ID: 'offline-incremental-profile' };
const originalFetch = globalThis.fetch;
let requestHashes = [];
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
const fetchImpl = async (_url, init) => {
  requestHashes.push(sha(init.body));
  const body = JSON.parse(init.body);
  return new Response(JSON.stringify({ model: env.PERCH_MODEL_ID,
    answers: Object.fromEntries(Object.entries(body.questions).map(([name, question]) => [name, fixedAnswer(name, question)])),
  }));
};
const measurements = [];
async function measure(kind, phase) {
  requestHashes = [];
  let result;
  const started = performance.now();
  const options = { root: fixture, env, stdout: text => { result = JSON.parse(text); }, stderr: () => {} };
  const code = kind === 'scan' ? await runPerch(['scan', '--incremental'], options)
    : await runStyleRanking(['--live', '--all', '--incremental', '--json'], { ...options, fetchImpl });
  const wall_ms = performance.now() - started;
  const identity = kind === 'scan'
    ? result.issues.map(({ id, path, rule, kind, broken, line, end_line }) => ({ id, path, rule, kind, broken, line, end_line }))
    : result.rows.map(({ target, state_sha256, model, answers }) => ({ target, state_sha256, model, answers }));
  const coverage = kind === 'scan' ? {
    methods: result.run.methods, checked: result.run.reviewed_checks ?? result.run.checked,
    failed: result.run.failed.length, incomplete: result.run.incomplete?.length ?? 0,
    supported: result.parser_coverage.supported, parsed: result.parser_coverage.parsed,
    parse_failures: result.parser_coverage.parse_failures,
  } : result.coverage;
  const measurement = {
    kind, phase, code, wall_ms, provider_requests: requestHashes.length,
    request_set_sha256: sha(JSON.stringify(requestHashes.sort())),
    result_sha256: sha(JSON.stringify(identity.sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b))))),
    coverage, carried: kind === 'scan' ? result.run.carried : result.reused_units,
    parser_coverage: kind === 'scan' ? result.parser_coverage : undefined,
    preflight_snapshot: result.preflight_snapshot, timings: result.timings,
    incremental_cache: result.incremental_cache,
  };
  if (phase !== 'cold') {
    const baseline = measurements.find(row => row.kind === kind && row.phase === 'cold');
    assert.equal(requestHashes.length, 0, `${kind}: unchanged model inputs must need zero HTTP requests`);
    assert.equal(measurement.result_sha256, baseline.result_sha256, `${kind}: cache must retain the same current verdicts`);
    assert.deepEqual(coverage, baseline.coverage, `${kind}: cache must not reduce coverage`);
    assert.equal(code, baseline.code, `${kind}: cache must preserve attention/failure status`);
  } else assert.ok(requestHashes.length > 0, `${kind}: cold run must exercise the provider path`);
  measurements.push(measurement);
  process.stdout.write(JSON.stringify({ kind, phase, wall_ms, provider_requests: requestHashes.length, carried: measurement.carried, code }) + '\n');
}
try {
  // Archive only committed files; never copy .env, caches, or another chat's work.
  execFileSync('tar', ['-xf', '-'], { cwd: fixture,
    input: execFileSync('git', ['archive', 'HEAD'], { cwd: root, maxBuffer: 256 * 1024 * 1024 }) });
  git('init', '-q', '-b', 'main'); git('add', '--force', '.'); commit('Frozen profile source');
  globalThis.fetch = fetchImpl;
  for (const phase of ['cold', 'unchanged', 'documentation-only-commit']) {
    if (phase === 'documentation-only-commit') {
      await writeFile(join(fixture, 'incremental-profile-note.md'), '# Offline cache exercise\n');
      git('add', 'incremental-profile-note.md'); commit('Documentation-only cache exercise');
    }
    await measure('scan', phase);
    await measure('style', phase);
  }
  const files = [
    'scripts/perch-workflow.mjs', 'scripts/perch-style.mjs', 'scripts/perch-style-cache.mjs', 'scripts/perch-throughput-patch.mjs',
    'scripts/profile-perch-incremental.mjs', 'node_modules/@lakeday/perch/dist/cli.mjs', 'perch-style.json',
  ];
  const report = {
    schema: 1, at: new Date().toISOString(), live: false, node: process.version,
    source_revision: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    tooling_sha256: Object.fromEntries(await Promise.all(files.map(async path => [path, sha(await readFile(join(root, path)))]))),
    measurements,
    note: 'Full committed source inventory in a disposable Git fixture; current tooling modules. Fixed offline answers validate requests, reuse and unchanged coverage only, not semantic/style quality or live latency. No network calls. Cold and warm retain existing parser failures and their nonzero exit. Timings include receipt/cache writes, exclude module import and fixture construction.',
  };
  await writeFile(output, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
} finally {
  globalThis.fetch = originalFetch;
  await rm(fixture, { recursive: true, force: true });
}
