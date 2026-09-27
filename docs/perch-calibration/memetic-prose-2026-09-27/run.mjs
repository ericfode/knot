#!/usr/bin/env node
// Bounded prose transfer probe; production questions and evaluator are unchanged.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluateStyle, validateScore } from '../../../scripts/perch-style.mjs';
import { styleEndpoint } from '../../../scripts/perch-style-cache.mjs';

const HERE = dirname(fileURLToPath(import.meta.url)), ROOT = resolve(HERE, '../../..');
const hash = value => createHash('sha256').update(value).digest('hex');
const save = (path, data) => writeFile(resolve(HERE, path), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
const load = async path => JSON.parse(await readFile(resolve(HERE, path), 'utf8'));
const mode = process.argv[2];
assert.ok(['freeze', 'live', 'verify'].includes(mode), 'Use freeze, live or verify');
const caseBytes = await readFile(resolve(HERE, 'cases.json'));
const corpus = JSON.parse(caseBytes), protocol = corpus.protocol;
const policyBytes = await readFile(resolve(ROOT, 'perch-style.json'));
const config = JSON.parse(policyBytes);
const rubrics = [...config.dimensions, ...config.diagnostic_dimensions];
assert.deepEqual(rubrics.map(r => r.id), protocol.dimensions);
const targets = [...config.style_targets, ...config.criticality.diagnostic_targets];
assert.ok(targets.every(t => t.level === protocol.target_level && t.minimum_probability === protocol.minimum_probability));
const questions = Object.fromEntries(rubrics.map(r => [r.id, {type: 'score', instructions: r.instructions, criteria: r.levels}]));
const candidates = corpus.cases.map(c => {
  const state = {kind: 'prose_passage', contract: c.purpose, source: c.text, instruction: protocol.instruction};
  return {target: c.id, kind: 'prose_passage', source_sha256: hash(c.text), state_sha256: hash(JSON.stringify(state)),
    context: {basis: 'bounded-prose-excerpt', files: [], unresolved: [], truncated: false}, state};
});
const requests = candidates.map(c => ({model: protocol.model, state: c.state, questions}));
const identities = {
  cases_sha256: hash(caseBytes), policy_sha256: hash(policyBytes),
  evaluator_sha256: hash(await readFile(resolve(ROOT, 'scripts/perch-style.mjs'))),
  runner_sha256: hash(await readFile(fileURLToPath(import.meta.url))),
  requests: candidates.map((c, i) => ({id: c.target, source_sha256: c.source_sha256,
    state_sha256: c.state_sha256, request_sha256: hash(JSON.stringify(requests[i]))})),
};
const project = corpus.cases.find(c => c.kind === 'project_probe');
assert.ok((await readFile(resolve(ROOT, project.origin.path), 'utf8')).includes(project.text), 'Project excerpt drifted');

if (mode === 'freeze') {
  await mkdir(resolve(HERE, 'requests')); // Reserve this experiment before any provider call.
  await save('rubric.json', config);
  for (const [i, c] of candidates.entries()) await save(`requests/${c.target}.json`, requests[i]);
  await save('freeze.json', {schema: 1, frozen_at: new Date().toISOString(),
    revision: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: ROOT, encoding: 'utf8'}).trim(), ...identities});
  console.log(JSON.stringify({status: 'frozen', specimens: candidates.length, questions_per_specimen: rubrics.length,
    policy_sha256: identities.policy_sha256, provider_requests: 0}));
  process.exit(0);
}

const frozen = await load('freeze.json');
for (const [key, value] of Object.entries(identities)) assert.deepEqual(frozen[key], value, `Frozen ${key} changed`);
assert.deepEqual(await load('rubric.json'), config);
for (const [i, c] of candidates.entries()) assert.deepEqual(await load(`requests/${c.target}.json`), requests[i]);
const assess = row => Object.fromEntries(targets.map(t => {
  const answer = row.answers[t.dimension];
  const total = Object.values(answer.probabilities).reduce((a, b) => a + b, 0);
  const mass = Object.entries(answer.probabilities).reduce((sum, [n, p]) => sum + (Number(n) >= t.level ? p : 0), 0) / total;
  return [t.dimension, {probability_at_target: mass, target_level: t.level,
    status: mass >= t.minimum_probability ? 'meets_target' : mass <= 1 - t.minimum_probability ? 'below_target' : 'uncertain'}];
}));

if (mode === 'verify') {
  const result = await load('results.json');
  assert.equal(result.freeze_sha256, hash(await readFile(resolve(HERE, 'freeze.json'))));
  assert.equal(result.status, 'complete');
  assert.equal(result.rows.length, candidates.length);
  assert.equal(result.transport.requests, candidates.length);
  assert.equal(result.transport.responses, candidates.length);
  for (const row of result.rows) {
    const index = candidates.findIndex(c => c.target === row.target);
    assert.ok(index >= 0);
    assert.equal(row.model, protocol.model);
    assert.equal(row.source_sha256, candidates[index].source_sha256);
    assert.equal(row.state_sha256, candidates[index].state_sha256);
    for (const r of rubrics) validateScore({...row.answers[r.id], type: 'score'}, r.levels.length);
    assert.deepEqual(row.assessments, assess(row));
    const receipt = await load(`responses/${row.target}.json`);
    assert.equal(receipt.request_sha256, identities.requests[index].request_sha256);
    assert.equal(receipt.response_sha256, hash(JSON.stringify(receipt.body)));
    for (const r of rubrics) assert.deepEqual(row.answers[r.id], validateScore(receipt.body.answers[r.id], r.levels.length));
  }
  assert.equal(new Set(result.rows.map(r => r.target)).size, candidates.length);
  console.log(JSON.stringify({status: 'verified', specimens: candidates.length, distributions: candidates.length * rubrics.length,
    requests_match_production_questions: true, historical_uptake_is_not_a_model_input: true}));
  process.exit(0);
}

assert.ok(process.env.PERCH_API_KEY || process.env.TYPESAFE_API_KEY, 'Credential unavailable');
await mkdir(resolve(HERE, 'responses')); // Existing/failed runs are never rerolled.
const endpoint = styleEndpoint(process.env.PERCH_BASE_URL || undefined);
const startedAt = new Date().toISOString(), started = performance.now();
const transport = {requests: 0, responses: 0}, rows = [];
let next = 0, failure = null;
const fetchImpl = async (url, options) => {
  const i = next++;
  assert.equal(hash(options.body), identities.requests[i].request_sha256, 'Evaluator request differs from frozen input');
  const response = await fetch(url, options);
  if (response.ok) {
    const body = await response.clone().json();
    await save(`responses/${candidates[i].target}.json`, {
      request_sha256: hash(options.body), response_sha256: hash(JSON.stringify(body)), body,
    });
  } // Never persist provider error text or authorization headers.
  return response;
};
try {
  await evaluateStyle(candidates, config, {
    env: {...process.env, PERCH_MODEL_ID: protocol.model}, fetchImpl, transport,
    concurrency: protocol.concurrency, expectedModel: protocol.model, rubrics,
    onRow: row => rows.push({...row, assessments: assess(row)}),
    onProgress: (done, count) => console.log(`${done}/${count} complete`),
  });
} catch (error) {
  failure = error.message;
}
await save('results.json', {schema: 1, status: failure ? 'failed' : 'complete', failure,
  started_at: startedAt, finished_at: new Date().toISOString(), elapsed_ms: Math.round(performance.now() - started),
  freeze_sha256: hash(await readFile(resolve(HERE, 'freeze.json'))), policy_sha256: identities.policy_sha256,
  endpoint_sha256: endpoint.sha256, requested_model: protocol.model, transport, rows});
console.log(JSON.stringify({status: failure ? 'failed' : 'complete', completed: rows.length, transport, failure}));
if (failure) process.exitCode = 1;
