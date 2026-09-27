#!/usr/bin/env node
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { evaluateStyle, validateScore } from '../../../scripts/perch-style.mjs';
import { styleEndpoint } from '../../../scripts/perch-style-cache.mjs';

const HERE = dirname(fileURLToPath(import.meta.url)), ROOT = resolve(HERE, '../../..');
const OLD = resolve(HERE, '../memetic-prose-2026-09-27');
const hash = value => createHash('sha256').update(value).digest('hex');
const load = async path => JSON.parse(await readFile(path, 'utf8'));
const save = (path, value) => writeFile(resolve(HERE, path), JSON.stringify(value, null, 2) + '\n', {flag: 'wx'});
const mode = process.argv[2];
assert.ok(['freeze', 'live', 'verify'].includes(mode));
const caseBytes = await readFile(resolve(HERE, 'cases.json')), corpus = JSON.parse(caseBytes);
const policies = {v5: await load(resolve(OLD, 'rubric.json')),
  v6: await load(resolve(HERE, mode === 'freeze' ? '../../../perch-style.json' : 'rubric-v6.json'))};
const stripped = policy => {
  const clone = structuredClone(policy);
  delete clone.version;
  clone.dimensions = clone.dimensions.filter(d => d.id !== 'highly_memetic');
  delete clone.style_role.composition_instructions;
  return clone;
};
assert.deepEqual(stripped(policies.v5), stripped(policies.v6), 'Unrelated rubric or targets changed');
const model = corpus.protocol.requested_model;
const questions = policy => [...policy.dimensions, ...policy.diagnostic_dimensions];
const jobs = Object.entries(policies).flatMap(([version, policy]) => corpus.cases.map(c => {
  const request = {model, state: c.state, questions: Object.fromEntries(questions(policy).map(d =>
    [d.id, {type: 'score', instructions: d.instructions, criteria: d.levels}]))};
  return {id: `${version}-${c.id}`, version, specimen: c.id, prior_id: version === 'v5' ? c.prior_id : null,
    request, request_sha256: hash(JSON.stringify(request))};
}));
const identity = {cases_sha256: hash(caseBytes),
  policies: Object.fromEntries(Object.entries(policies).map(([version, policy]) => [version, hash(JSON.stringify(policy))])),
  evaluator_sha256: hash(await readFile(resolve(ROOT, 'scripts/perch-style.mjs'))),
  runner_sha256: hash(await readFile(fileURLToPath(import.meta.url))),
  requests: jobs.map(({id, request_sha256}) => ({id, request_sha256}))};

if (mode === 'freeze') {
  await mkdir(resolve(HERE, 'requests'));
  await save('rubric-v6.json', policies.v6);
  for (const job of jobs) await save(`requests/${job.id}.json`, job.request);
  await save('freeze.json', {at: new Date().toISOString(), ...identity});
  console.log(JSON.stringify({status: 'frozen', requests: jobs.length, fresh_expected: 6, exact_prior_reuse_expected: 2}));
  process.exit(0);
}
const frozen = await load(resolve(HERE, 'freeze.json'));
for (const [key, value] of Object.entries(identity)) assert.deepEqual(frozen[key], value);
for (const job of jobs) assert.deepEqual(await load(resolve(HERE, `requests/${job.id}.json`)), job.request);
const assess = answers => Object.fromEntries(Object.entries(answers).map(([id, answer]) => {
  const total = Object.values(answer.probabilities).reduce((sum, p) => sum + p, 0);
  const mass = Object.entries(answer.probabilities).reduce((sum, [level, p]) => sum + (Number(level) >= 3 ? p : 0), 0) / total;
  return [id, {probability_at_target: mass, status: mass >= 0.6 ? 'meets_target' : mass <= 0.4 ? 'below_target' : 'uncertain'}];
}));
const validated = (body, version) => {
  assert.equal(body.model, model);
  return Object.fromEntries(questions(policies[version]).map(d => [d.id, validateScore(body.answers[d.id], d.levels.length)]));
};
if (mode === 'verify') {
  const result = await load(resolve(HERE, 'results.json'));
  assert.equal(result.status, 'complete');
  assert.equal(result.rows.length, jobs.length);
  assert.equal(result.freeze_sha256, hash(await readFile(resolve(HERE, 'freeze.json'))));
  for (const [i, row] of result.rows.entries()) {
    const job = jobs[i];
    assert.equal(row.id, job.id);
    const receipt = await load(resolve(HERE, `responses/${job.id}.json`));
    assert.equal(receipt.request_sha256, job.request_sha256);
    assert.equal(receipt.response_sha256, hash(JSON.stringify(receipt.body)));
    assert.deepEqual(row.answers, validated(receipt.body, job.version));
    assert.deepEqual(row.assessments, assess(row.answers));
  }
  console.log(JSON.stringify({status: 'verified', policy_comparisons: 8, distributions: 40,
    fresh_provider_requests: result.transport.requests, reused: result.reused, other_axes_and_targets_unchanged: true}));
  process.exit(0);
}
assert.deepEqual(await load(resolve(ROOT, 'perch-style.json')), policies.v6, 'Current rubric drifted');
assert.ok(process.env.PERCH_API_KEY || process.env.TYPESAFE_API_KEY, 'Credential unavailable');
await mkdir(resolve(HERE, 'responses'));
const transport = {requests: 0, responses: 0}, rows = [];
const started = performance.now(), startedAt = new Date().toISOString();
let reused = 0, failure = null;
try {
  for (const job of jobs) {
    let body, origin;
    if (job.prior_id) {
      const previous = await load(resolve(OLD, `responses/${job.prior_id}.json`));
      assert.equal(previous.request_sha256, job.request_sha256, 'Prior request is not identical');
      assert.equal(previous.response_sha256, hash(JSON.stringify(previous.body)));
      body = previous.body; origin = `../memetic-prose-2026-09-27/responses/${job.prior_id}.json`; reused++;
    } else {
      const state = job.request.state;
      const candidate = {target: job.id, kind: 'prose_passage', state,
        source_sha256: hash(state.source), state_sha256: hash(JSON.stringify(state)),
        context: {basis: 'bounded-prose-excerpt', files: [], unresolved: [], truncated: false}};
      await evaluateStyle([candidate], policies[job.version], {
        env: {...process.env, PERCH_MODEL_ID: model}, transport, concurrency: 1, expectedModel: model,
        rubrics: questions(policies[job.version]), fetchImpl: async (url, options) => {
          assert.equal(hash(options.body), job.request_sha256);
          const response = await fetch(url, options);
          if (response.ok) body = await response.clone().json();
          return response;
        },
      });
      origin = 'fresh-provider-response';
    }
    const answers = validated(body, job.version);
    await save(`responses/${job.id}.json`, {request_sha256: job.request_sha256,
      response_sha256: hash(JSON.stringify(body)), origin, body});
    rows.push({id: job.id, version: job.version, specimen: job.specimen, model: body.model,
      origin, answers, assessments: assess(answers)});
    console.log(`${job.id} complete (${origin === 'fresh-provider-response' ? 'fresh' : 'exact prior reuse'})`);
  }
} catch (error) { failure = error.message; }
await save('results.json', {status: failure ? 'failed' : 'complete', failure,
  started_at: startedAt, elapsed_ms: Math.round(performance.now() - started), requested_model: model,
  endpoint_sha256: styleEndpoint(process.env.PERCH_BASE_URL || undefined).sha256,
  freeze_sha256: hash(await readFile(resolve(HERE, 'freeze.json'))), transport, reused, rows});
if (failure) { console.error(failure); process.exitCode = 1; }
