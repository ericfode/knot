import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { reviewManifest } from './review.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const hash = value => createHash('sha256').update(value).digest('hex');
const SOURCE = 'def head(x: U32) -> U32:\n  x\n\ndef main() -> U32:\n  head(1)\n';
const policy = JSON.parse(await readFile(resolve(HERE, 'config.json'), 'utf8'));
const save = (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n');

async function fixture(t, sources = [SOURCE], extra = {}) {
  const root = await mkdtemp(resolve(tmpdir(), 'life-helper-review-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const entries = [];
  for (let i = 0; i < sources.length; i++) {
    const source = `specimen-${i}.bend.snapshot`;
    await writeFile(resolve(root, source), sources[i]);
    entries.push({ id: `private-arm-a-${i}`, source, source_sha256: hash(sources[i]), deterministic_passed: true, semantic_clean: true,
      author: 'gpt-6-astra', condition: 'blueberry', legacy_receipt: 'not-read-old-scores.json', ...extra });
  }
  const manifestPath = resolve(root, 'manifest.json'), configPath = resolve(root, 'config.json'), output = resolve(root, 'output');
  await save(manifestPath, { root, entries }); await save(configPath, policy);
  return { root, entries, manifestPath, configPath, output, jobs: 2, live: true, loadEnv: false, env: { TYPESAFE_API_KEY: 'mock-secret' } };
}

function answer(levels, score = levels - 1) {
  const probabilities = Object.fromEntries(Array.from({ length: levels }, (_, index) => [String(index), index === score ? 1 : 0]));
  return { type: 'score', score, confidence: 1, probabilities };
}

function provider(transform = body => body) {
  const calls = [];
  const fetchImpl = async (url, options) => {
    const request = JSON.parse(options.body);
    calls.push({ url, options, request });
    const body = { model: 'jev-1.13.0', usage: { input_tokens: 10, output_tokens: 2 },
      answers: Object.fromEntries(Object.entries(request.questions).map(([id, q]) => [id, answer(q.criteria.length)])) };
    const result = await transform(body, request, calls.length);
    return result instanceof Response ? result : new Response(JSON.stringify(result), { status: 200 });
  };
  return { calls, fetchImpl };
}

test('complete composition plus every declaration, exact anonymous requests and receipts', async t => {
  const f = await fixture(t), p = provider();
  const { report, report_path } = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(p.calls.length, 3);
  assert.equal(report.status, 'complete');
  assert.equal(report.summary.full_pass, 1);
  assert.equal(report.entries[0].coverage.required_assessments, 7);
  assert.equal(report.entries[0].support_assessments.length, 2);
  assert.deepEqual(report.entries[0].support_assessments.map(a => a.declaration.name), ['head', 'main']);
  assert.equal(report.transport.provider_requests, 3);
  assert.equal(report.usage.fresh.input_tokens, 30);
  assert.equal(report.usage.fresh.output_tokens, 6);
  assert.ok(report.transport.peak_in_flight <= 2);
  for (const call of p.calls) {
    assert.equal(call.request.model, 'jev-1.13.0');
    assert.equal(call.request.state.source, SOURCE);
    assert.equal(call.request.state.path, 'composition.bend');
    assert.equal(call.request.state.contract, policy.contract);
    assert.equal(call.request.state.context_complete, true);
    assert.ok(!JSON.stringify(call.request).includes(f.root));
    assert.ok(!JSON.stringify(call.request).includes('private-arm-a'));
    assert.ok(!JSON.stringify(call.request).includes('blueberry'));
    assert.ok(!JSON.stringify(call.request).includes('gpt-6-astra'));
    assert.ok(!JSON.stringify(call.request).includes('not-read-old-scores'));
    assert.equal(call.request.state.declarations.some(d => 'name' in d), false);
  }
  for (const request of report.requests) {
    const dir = dirname(request.receipt_path), receipt = JSON.parse(await readFile(request.receipt_path));
    assert.equal(receipt.response_sha256, hash(await readFile(resolve(dir, 'response.txt'))));
    assert.equal(receipt.identity.request_sha256, hash(await readFile(resolve(dir, 'request.json'))));
    assert.equal(receipt.identity.state_sha256, hash(await readFile(resolve(dir, 'state.json'))));
    assert.ok(!JSON.stringify(receipt).includes('mock-secret'));
  }
  assert.equal(JSON.parse(await readFile(report_path)).run_id, report.run_id);
});

test('exact duplicate source shares requests; immutable run replay charges zero new usage', async t => {
  const f = await fixture(t, [SOURCE, SOURCE]), p = provider();
  const first = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(first.report.summary.logical_requests, 6);
  assert.equal(first.report.summary.unique_requests, 3);
  assert.equal(p.calls.length, 3);
  const before = await readFile(first.report_path);
  const replay = await reviewManifest({ ...f, fetchImpl: () => assert.fail('no replay network call') });
  assert.equal(replay.replayed_run, true);
  assert.equal(replay.invocation.input_tokens, 0);
  assert.equal(replay.invocation.provider_requests, 0);
  assert.deepEqual(await readFile(first.report_path), before);
});

test('new manifest reuses exact complete requests with saved model evidence and no double counting', async t => {
  const f = await fixture(t), p = provider();
  await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  await save(f.manifestPath, { root: f.root, entries: [{ ...f.entries[0], id: 'different-private-condition', semantic_clean: null }] });
  const replay = await reviewManifest({ ...f, fetchImpl: () => assert.fail('cached request must not reroll') });
  assert.equal(replay.report.summary.reused_requests, 3);
  assert.equal(replay.report.transport.provider_requests, 0);
  assert.equal(replay.report.usage.fresh.input_tokens, 0);
  assert.equal(replay.report.usage.reused.input_tokens, 30);
  assert.equal(replay.report.entries[0].family_assessments[0].model_evidence, 'saved_provider_response');
  assert.equal(replay.report.summary.full_pass, 0);
  assert.equal(replay.report.entries[0].semantic_clean, null);
});

test('below-target family stays nonpass despite perfect support and cannot be rerolled', async t => {
  const f = await fixture(t), p = provider((body, request) => {
    if (request.questions.maximally_big_brain) body.answers.maximally_big_brain = answer(6, 4);
    return body;
  });
  const first = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(first.report.entries[0].family_passed, false);
  assert.equal(first.report.entries[0].support_passed, true);
  assert.equal(first.report.summary.full_pass, 0);
  assert.equal(first.report.entries[0].family_assessments[0].target_probability, 0);
  await save(f.manifestPath, { root: f.root, entries: [{ ...f.entries[0], id: 'another-name' }] });
  const again = await reviewManifest({ ...f, fetchImpl: () => assert.fail('nonpass must reuse') });
  assert.equal(again.report.summary.full_pass, 0);
  assert.equal(again.report.summary.reused_requests, 3);
});

test('one unsupported declaration prevents pass without changing whole-family scores', async t => {
  const f = await fixture(t), p = provider((body, request) => {
    if (request.state.focus.id === 'D002') body.answers.supports_main_idea = answer(5, 1);
    return body;
  });
  const { report } = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(report.entries[0].family_passed, true);
  assert.equal(report.entries[0].support_passed, false);
  assert.equal(report.summary.full_pass, 0);
  assert.equal(report.entries[0].family_assessments[0].score, 5);
});

test('uncertain target mass remains nonpass and raw probability distribution is retained', async t => {
  const f = await fixture(t), p = provider((body, request) => {
    if (request.questions.maximally_big_brain) body.answers.maximally_big_brain = {
      type: 'score', score: 4.5, confidence: 0.8, probabilities: { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0.5, 5: 0.5 } };
    return body;
  });
  const { report } = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  const a = report.entries[0].family_assessments[0];
  assert.equal(a.status, 'uncertain'); assert.equal(a.target_probability, 0.5);
  assert.equal(a.probabilities['5'], 0.5); assert.equal(report.summary.full_pass, 0);
});

test('fixed false or unavailable gates remain nonpasses even with complete style success', async t => {
  const f = await fixture(t, [SOURCE, SOURCE, SOURCE]);
  f.entries[0].deterministic_passed = false;
  f.entries[1].semantic_clean = null;
  delete f.entries[2].semantic_clean;
  await save(f.manifestPath, { root: f.root, entries: f.entries });
  const { report } = await reviewManifest({ ...f, fetchImpl: provider().fetchImpl });
  assert.equal(report.summary.complete_entries, 3);
  assert.equal(report.summary.family_passed, 3); assert.equal(report.summary.full_pass, 0);
  assert.deepEqual(report.entries.map(e => e.semantic_clean), [true, null, null]);
});

test('syntax, empty, bad hash and labelled entries are preflight nonpasses while valid entries continue', async t => {
  const f = await fixture(t, [SOURCE, 'def broken(:\n', '', SOURCE, `# condition: treatment\n${SOURCE}`]);
  f.entries[3].source_sha256 = '0'.repeat(64);
  await save(f.manifestPath, { root: f.root, entries: f.entries });
  const p = provider(), { report } = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(p.calls.length, 3);
  assert.equal(report.status, 'complete');
  assert.equal(report.failure, null);
  assert.equal(report.summary.preflight_rejected, 4);
  assert.equal(report.summary.full_pass, 1);
  assert.deepEqual(report.entries.slice(1).map(e => e.errors[0]), ['parser_parse-error', 'empty_source', 'source_hash_mismatch', 'experimental_label_in_source']);
  assert.equal(report.entries[1].family_assessments.every(a => a.status === 'unavailable'), true);
});

test('source and declaration caps reject before transport', async t => {
  const f = await fixture(t, [SOURCE]);
  await save(f.configPath, { ...policy, max_source_bytes: 10 });
  let result = await reviewManifest({ ...f, fetchImpl: () => assert.fail('oversize source call') });
  assert.equal(result.report.entries[0].errors[0], 'source_limit');
  await save(f.configPath, { ...policy, max_declarations: 1 });
  result = await reviewManifest({ ...f, fetchImpl: () => assert.fail('too many declarations call') });
  assert.equal(result.report.entries[0].errors[0], 'declaration_limit');
});

test('strict resolved-model mismatch retains raw failure and stops later dispatch; cannot retry', async t => {
  const f = await fixture(t), p = provider(body => ({ ...body, model: 'jev-other' }));
  const { report } = await reviewManifest({ ...f, jobs: 1, fetchImpl: p.fetchImpl });
  assert.equal(p.calls.length, 1);
  assert.equal(report.status, 'incomplete');
  assert.equal(report.failure, 'resolved_model_mismatch');
  assert.equal(report.entries[0].coverage.complete, false);
  assert.equal(report.summary.full_pass, 0);
  assert.equal(report.requests[0].receipt.resolved_model, 'jev-other');
  assert.ok((await readFile(resolve(dirname(report.requests[0].receipt_path), 'response.txt'), 'utf8')).includes('jev-other'));
  await save(f.manifestPath, { root: f.root, entries: [{ ...f.entries[0], id: 'new-name' }] });
  const retry = await reviewManifest({ ...f, fetchImpl: () => assert.fail('failed identities cannot retry') });
  assert.equal(retry.report.failure, 'previous_attempt_failed');
  assert.equal(retry.report.transport.provider_requests, 0);
});

test('HTTP output, invalid JSON, missing model and incomplete distributions are retained nonpasses', async t => {
  const cases = [
    [() => new Response('unavailable body', { status: 503 }), 'provider_http_error'],
    [() => new Response('{', { status: 200 }), 'provider_invalid_json'],
    [body => { delete body.model; return body; }, 'resolved_model_missing'],
    [body => { delete body.answers.maximally_big_brain.probabilities['5']; return body; }, 'provider_invalid_score'],
    [body => { delete body.answers.payoff; return body; }, 'provider_invalid_score'],
  ];
  for (const [transform, error] of cases) {
    const f = await fixture(t), p = provider(transform);
    const { report } = await reviewManifest({ ...f, jobs: 1, fetchImpl: p.fetchImpl });
    assert.equal(report.failure, error); assert.equal(p.calls.length, 1);
    assert.equal(report.entries[0].coverage.complete, false);
    assert.equal(report.summary.full_pass, 0);
    assert.ok((await readFile(resolve(dirname(report.requests[0].receipt_path), 'response.txt'))).length > 0);
  }
});

test('transport errors redact exception text and retain attempt without retry', async t => {
  const f = await fixture(t);
  const result = await reviewManifest({ ...f, jobs: 1, fetchImpl: () => { throw Error('mock-secret https://private.example/key'); } });
  assert.equal(result.report.failure, 'provider_transport_failure');
  assert.ok(!JSON.stringify(result.report).includes('mock-secret'));
  assert.ok(!JSON.stringify(result.report).includes('private.example'));
  assert.equal(result.report.requests[0].receipt.response_sha256, null);
  assert.equal(result.report.requests[0].receipt.model_evidence, 'not_reported');
});

test('corrupt cached response is unavailable, never silently rerolled', async t => {
  const f = await fixture(t), p = provider();
  const first = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  const dir = dirname(first.report.requests[0].receipt_path);
  await writeFile(resolve(dir, 'response.txt'), '{}');
  await save(f.manifestPath, { root: f.root, entries: [{ ...f.entries[0], id: 'changed-metadata' }] });
  const { report } = await reviewManifest({ ...f, fetchImpl: () => assert.fail('corruption cannot reroll') });
  assert.equal(report.failure, 'receipt_response_mismatch');
  assert.equal(report.summary.full_pass, 0);
  assert.equal(report.transport.provider_requests, 0);
});

test('an interrupted reservation blocks network even under a new manifest', async t => {
  const f = await fixture(t);
  const dry = await reviewManifest({ ...f, live: false, fetchImpl: () => assert.fail('offline call') });
  const requestId = dry.report.requests[0].id;
  await mkdir(resolve(f.output, 'requests', requestId));
  const { report } = await reviewManifest({ ...f, fetchImpl: () => assert.fail('interrupted call cannot reroll') });
  assert.equal(report.failure, 'previous_attempt_incomplete');
  assert.equal(report.transport.provider_requests, 0);
  assert.equal(report.summary.full_pass, 0);
});

test('a changed contract changes requests; author metadata alone does not', async t => {
  const f = await fixture(t), p = provider();
  const first = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  await save(f.configPath, { ...policy, contract: policy.contract + ' This is an independent policy identity.' });
  const second = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(p.calls.length, 6);
  assert.equal(second.report.summary.reused_requests, 0);
  assert.notEqual(first.report.requests[0].id, second.report.requests[0].id);
  await save(f.configPath, { ...policy, model: 'jev-latest' });
  await assert.rejects(reviewManifest({ ...f, fetchImpl: () => assert.fail('invalid model call') }), /invalid_policy_model_or_contract/);
});

test('source-byte change without a new source identity rejects instead of reusing', async t => {
  const f = await fixture(t), p = provider();
  await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  await writeFile(resolve(f.root, f.entries[0].source), SOURCE + '\n');
  const { report } = await reviewManifest({ ...f, fetchImpl: () => assert.fail('changed source call') });
  assert.equal(report.entries[0].errors[0], 'source_hash_mismatch');
  assert.equal(report.summary.full_pass, 0);
});

test('offline preflight and missing credentials make no provider calls and cannot pass', async t => {
  const f = await fixture(t);
  const dry = await reviewManifest({ ...f, live: false, env: {}, fetchImpl: () => assert.fail('offline call') });
  assert.equal(dry.report.status, 'preflight'); assert.equal(dry.report.summary.full_pass, 0);
  assert.equal(dry.report.transport.provider_requests, 0);
  const missing = await reviewManifest({ ...f, env: {}, fetchImpl: () => assert.fail('credentialless call') });
  assert.equal(missing.report.failure, 'credential_unavailable');
  assert.equal(missing.report.summary.full_pass, 0);
});

test('concurrent provider failure drains started requests and never dispatches remaining work', async t => {
  const f = await fixture(t);
  let count = 0;
  const p = provider(async body => {
    count++;
    if (count === 1) return new Response('stop', { status: 503 });
    await new Promise(resolve => setTimeout(resolve, 10));
    return body;
  });
  const { report } = await reviewManifest({ ...f, jobs: 2, fetchImpl: p.fetchImpl });
  assert.equal(p.calls.length, 2);
  assert.equal(report.transport.peak_in_flight, 2);
  assert.equal(report.requests.filter(r => r.status === 'complete').length, 1);
  assert.equal(report.requests.filter(r => r.error === 'dispatch_stopped').length, 1);
  assert.equal(report.summary.full_pass, 0);
});

test('actual parser includes datatype, law/proof unit and entrypoint without name exemptions', async t => {
  const source = `import Base
type Box is Data:
  Box{value: U32}
law equal:
  for +n: U32
  {n == n : U32}
def equal(n): {==}
def main() -> U32: 1
`;
  const f = await fixture(t, [source]), p = provider();
  const { report } = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  assert.equal(report.summary.full_pass, 1);
  assert.equal(p.calls.length, 4);
  const declarations = report.entries[0].declarations;
  assert.deepEqual(declarations.map(d => d.name), ['Box', 'equal', 'main']);
  assert.equal(declarations[0].kind, 'bend_datatype');
  assert.equal(declarations[1].kind, 'bend_law_definition');
  assert.ok(declarations[1].law_span.end_byte > declarations[1].law_span.start_byte);
  assert.ok(p.calls.every(c => c.request.state.source === source));
});

test('same-run replay detects tampered receipts instead of returning a previous pass', async t => {
  const f = await fixture(t), p = provider();
  const first = await reviewManifest({ ...f, fetchImpl: p.fetchImpl });
  const path = first.report.requests[0].receipt_path;
  await writeFile(path, (await readFile(path, 'utf8')) + ' ');
  await assert.rejects(reviewManifest({ ...f, fetchImpl: () => assert.fail('tampered replay must not call') }), /run_receipt_changed/);
});
