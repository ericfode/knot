#!/usr/bin/env node
// One-shot task-only calibration through the production request constructor.
import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseEnv } from 'node:util';
import { potentialProfundityRequest, assessPotentialProfundity } from '../../../scripts/perch-style.mjs';
import { styleEndpoint } from '../../../scripts/perch-style-cache.mjs';
const HERE = dirname(fileURLToPath(import.meta.url)), ROOT = resolve(HERE, '../../..');
const hash = data => createHash('sha256').update(data).digest('hex');
const write = (path, data) => writeFile(path, typeof data === 'string' ? data : JSON.stringify(data, null, 2) + '\n', {flag:'wx'});
const stage = process.argv[2];
if (!['development', 'held_out', 'hypothesis_probe'].includes(stage)) throw new Error('Expected development, held_out or hypothesis_probe');
const policyBytes = await readFile(resolve(ROOT, 'perch-style.json'));
const config = JSON.parse(policyBytes);
const expectations = JSON.parse(await readFile(resolve(ROOT, 'tests/perch-potential/expectations.json')));
if (hash(policyBytes) !== expectations.policy.sha256) throw new Error('Policy changed after expectations');
const env = {...parseEnv(await readFile(resolve(ROOT, '.env'), 'utf8')), ...process.env};
const endpoint = styleEndpoint(env.PERCH_BASE_URL || undefined);
const key = env.PERCH_API_KEY || env.TYPESAFE_API_KEY;
if (!key) throw new Error('Credential unavailable');
const rows = [];
for (const control of expectations.controls.filter(c => c.stage === stage)) {
  const task = await readFile(resolve(ROOT, control.task), 'utf8');
  if (hash(task) !== control.task_sha256) throw new Error('Task changed after expectations');
  const request = potentialProfundityRequest(task, config, 'jev-1.13.0');
  const output = resolve(HERE, 'task-receipts', control.id);
  await mkdir(output); // Reservation: existing or failed identities never reroll.
  await write(resolve(output, 'request.json'), request.body);
  const startedAt = new Date().toISOString(), start = performance.now();
  let body = null, raw = null, response = null, assessment = null, failure = null;
  try {
    response = await fetch(endpoint.url, {method:'POST', signal:AbortSignal.timeout(30000),
      headers:{authorization:`Bearer ${key}`, 'content-type':'application/json'}, body:request.body});
    raw = await response.text();
    await write(resolve(output, 'response.json'), raw);
    if (!response.ok) throw new Error('provider_http_error');
    body = JSON.parse(raw);
    if (body.model !== 'jev-1.13.0') throw new Error('resolved_model_mismatch');
    assessment = assessPotentialProfundity(body.answers.potential_profundity, config);
  } catch (error) { failure = error.message; }
  const expectedStatus = {not_relevant:'low', relevant:'high'}[control.expected_class];
  const row = {id:control.id, stage, task_sha256:control.task_sha256,
    policy_sha256:hash(policyBytes), request_sha256:hash(request.body), state_sha256:request.state_sha256,
    endpoint_sha256:endpoint.sha256, response_sha256:raw === null ? null : hash(raw),
    started_at:startedAt, finished_at:new Date().toISOString(), elapsed_ms:Math.round(performance.now()-start),
    http_status:response?.status ?? null, requested_model:'jev-1.13.0', resolved_model:body?.model ?? null,
    usage:body?.usage ?? null, assessment, expected_class:control.expected_class,
    expectation_met:expectedStatus ? assessment?.status === expectedStatus : null,
    status:failure ? 'failed' : 'complete', failure};
  await write(resolve(output, 'receipt.json'), row);
  rows.push(row);
  console.log(JSON.stringify(row));
  if (failure) { process.exitCode=2; break; }
}
await write(resolve(HERE, `${stage}.json`), {stage, policy_sha256:hash(policyBytes), rows});
