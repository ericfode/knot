import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { assessPotentialProfundity, assessStyle, potentialProfundityRequest, prepareStyleComposition,
  prepareStyleTargets, runStyleRanking } from '../scripts/perch-style.mjs';

const config = JSON.parse(await readFile(new URL('./perch-style/v4.json', import.meta.url), 'utf8'));
const source = 'import Base\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: helper(x)\n';
const contract = 'Return the successor of an unsigned word modulo its range. Preserve the input convention.';
const sha = value => createHash('sha256').update(value).digest('hex');
const score = (level, levels) => ({ type: 'score', score: level, confidence: 1,
  probabilities: Object.fromEntries(Array.from({ length: levels }, (_, i) => [i, i === level ? 1 : 0])) });

async function fixture(t, content = source) {
  const root = await mkdtemp(join(tmpdir(), 'perch-potential-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  await writeFile(join(root, 'unit.bend'), content);
  await writeFile(join(root, 'contract.md'), contract);
  return root;
}

function provider({ potential = 4, composition = 5, grade = 3, criticality = 1, model = 'jev-1.13.0', hook } = {}) {
  const requests = [];
  const fetchImpl = async (_url, options) => {
    const request = JSON.parse(options.body);
    requests.push(request);
    const phase = request.questions.potential_profundity ? 'potential' : request.state.files ? 'composition' : 'declaration';
    const answers = Object.fromEntries(Object.entries(request.questions).map(([id, q]) => [id,
      id === 'potential_profundity' ? typeof potential === 'number' ? score(potential, q.criteria.length) : potential
        : id === 'criticality' ? score(criticality, 2) : score(phase === 'composition' ? composition : grade, q.criteria.length)]));
    const body = { model, answers, usage: { input_tokens: 12, output_tokens: 3 } };
    if (hook) await hook({ request, body, phase, count: requests.length });
    return { ok: true, json: async () => body };
  };
  return { requests, fetchImpl };
}

async function run(root, p, options = [], targets = ['unit.bend']) {
  const output = [], errors = [];
  const code = await runStyleRanking(['--live', '--json', ...options, ...targets], { root,
    env: { PERCH_API_KEY: 'offline-secret', PERCH_MODEL_ID: 'jev-1.13.0' }, fetchImpl: p.fetchImpl,
    stdout: line => output.push(line), stderr: line => errors.push(line) });
  return { code, report: JSON.parse(output[0]), errors };
}

test('task request is source-blind and exact production request precedes all source judgments', async t => {
  const root = await fixture(t), p = provider();
  const result = await run(root, p, ['--task=contract.md']);
  assert.equal(result.code, 0);
  assert.deepEqual(p.requests[0], JSON.parse(potentialProfundityRequest(contract, config, 'jev-1.13.0').body));
  assert.deepEqual(Object.keys(p.requests[0].state), ['contract', 'instruction']);
  assert.deepEqual(Object.keys(p.requests[0].questions), ['potential_profundity']);
  assert.ok(!JSON.stringify(p.requests[0]).includes('unit.bend'));
  assert.ok(!JSON.stringify(p.requests[0]).includes('def helper'));
  assert.equal(p.requests.length, 4);
  assert.equal(result.report.potential_profundity.task.sha256, sha(contract));
  assert.equal(result.report.potential_profundity.review.request_sha256, sha(JSON.stringify(p.requests[0])));
  assert.equal(result.report.potential_profundity.assessment.status, 'high');
  assert.equal(result.report.composition.assessment.status, 'meets_target');
  assert.equal(result.report.qualification.fully_qualified, true);
  assert.equal(result.report.provider_requests, 4);
});

test('high potential requires one complete composition Galaxy score, never individual helper novelty', async t => {
  const root = await fixture(t), p = provider();
  const { report, code } = await run(root, p, [`--cohort=${contract}`]);
  assert.equal(code, 0);
  const family = p.requests.filter(r => r.state.files);
  assert.equal(family.length, 1);
  assert.deepEqual(family[0].state.files, [{ path: 'unit.bend', source }]);
  assert.deepEqual(Object.keys(family[0].questions), ['maximally_big_brain']);
  assert.equal('potential_profundity' in family[0].state, false);
  assert.equal('answers' in family[0].state, false);
  assert.ok(report.criticality.assessments.every(a => a.status === 'critical'));
  assert.ok(report.assessments.filter(a => a.dimension === 'maximally_big_brain').every(a => a.target_level === 3 && a.target_basis === 'default'));
  assert.equal(report.rows[0].answers.maximally_big_brain.probabilities[3], 1);
  assert.equal(report.composition.review.row.answers.maximally_big_brain.probabilities[5], 1);
  assert.ok(report.assessments.filter(a => ['anticipation', 'payoff'].includes(a.dimension)).every(a => a.target_basis === 'criticality'));
});

test('low potential retains baseline standards and makes no composition provider call', async t => {
  const root = await fixture(t), p = provider({ potential: 1 });
  const { report, code } = await run(root, p, ['--task=contract.md']);
  assert.equal(code, 0); assert.equal(p.requests.length, 3);
  assert.equal(report.potential_profundity.assessment.status, 'low');
  assert.equal(report.composition.assessment.status, 'not_required');
  assert.equal(report.composition.review, null);
  assert.equal(report.qualification.fully_qualified, true);
  const bad = await run(root, provider({ potential: 0, grade: 2 }), ['--task=contract.md']);
  assert.equal(bad.code, 3); assert.equal(bad.report.qualification.fully_qualified, false);
});

test('missing and uncertain potential stay explicitly advisory without blocking baseline success', async t => {
  const root = await fixture(t), missing = provider();
  const a = await run(root, missing);
  assert.equal(a.code, 0); assert.equal(missing.requests.length, 2);
  assert.equal(a.report.potential_profundity.assessment.status, 'unavailable');
  assert.equal(a.report.potential_profundity.assessment.reason, 'missing_task_context');
  assert.equal(a.report.style_summary.meets_all, 2);
  assert.equal(a.report.qualification.fully_qualified, true);
  assert.equal(a.report.qualification.potential_advisory, true);
  const p = provider({ potential: { type: 'score', score: 2.5, confidence: .5, probabilities: { 0: 0, 1: 0, 2: .5, 3: .5, 4: 0 } } });
  const b = await run(root, p, ['--task=contract.md']);
  assert.equal(b.code, 0); assert.equal(p.requests.length, 3);
  assert.equal(b.report.potential_profundity.assessment.status, 'uncertain');
  assert.equal(b.report.composition.assessment.status, 'unavailable');
  assert.equal(b.report.qualification.potential_advisory, true);
  assert.equal(b.report.qualification.composition_required, false);
});

test('composition failure cannot borrow passing declaration scores; raw family distribution remains visible', async t => {
  const root = await fixture(t), p = provider({ composition: 4 });
  const { report, code } = await run(root, p, ['--task=contract.md']);
  assert.equal(code, 3); assert.equal(report.style_summary.meets_all, 2);
  assert.equal(report.composition.assessment.status, 'below_target');
  assert.equal(report.composition.review.row.answers.maximally_big_brain.probabilities[4], 1);
  assert.equal(report.qualification.fully_qualified, false);
});

test('full selected files and known collaborator files determine composition scope and identity', async t => {
  const root = await fixture(t, 'import Base\nimport ./helper.bend as H\ndef solve(x: U32) -> U32: H.next(x)\ndef other() -> U32: 7\n');
  await writeFile(join(root, 'helper.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,1)\n');
  const candidates = await prepareStyleTargets(['unit.bend::solve'], contract, config, root);
  const composition = await prepareStyleComposition(candidates, contract, config, root);
  assert.equal(composition.available, true, JSON.stringify(composition.reasons));
  assert.deepEqual(composition.candidate.context.files.map(f => f.path), ['helper.bend', 'unit.bend']);
  assert.deepEqual(composition.candidate.context.selected_files, ['unit.bend']);
  assert.match(composition.candidate.state.files[1].source, /def other/);
  const p = provider(), result = await run(root, p, ['--task=contract.md'], ['unit.bend::solve']);
  assert.equal(result.code, 0);
  assert.equal(p.requests[1].state.files.length, 2);
});

test('unknown references or bounded full-source overflow withhold composition qualification', async t => {
  const root = await fixture(t, 'import Base\ndef solve(x: U32) -> U32: absent(x)\n'), p = provider();
  const unknown = await run(root, p, ['--task=contract.md']);
  assert.equal(unknown.code, 3); assert.equal(unknown.report.composition.available, false);
  assert.ok(unknown.report.composition.reasons.includes('unresolved_composition_context'));
  assert.equal(p.requests.some(r => r.state.files), false);
  await writeFile(join(root, 'unit.bend'), source + '# ' + 'x'.repeat(48000) + '\n');
  const large = await run(root, provider(), ['--task=contract.md']);
  assert.equal(large.code, 3); assert.ok(large.report.composition.reasons.includes('composition_byte_limit'));
  assert.equal(large.report.composition.context.truncated, true);
});

test('task precedence, task byte limit and default generic cohort never establish low potential', async t => {
  const root = await fixture(t), p = provider({ potential: 0 });
  await run(root, p, ['--task=contract.md', '--cohort=Discard this competing description']);
  assert.equal(p.requests[0].state.contract, contract);
  await writeFile(join(root, 'contract.md'), 'x'.repeat(16001));
  const large = provider(), { code, report } = await run(root, large, ['--task=contract.md']);
  assert.equal(code, 0); assert.equal(report.potential_profundity.assessment.reason, 'task_byte_limit');
  assert.ok(large.requests.every(r => !r.questions.potential_profundity));
  assert.throws(() => potentialProfundityRequest('', config), /explicit bounded/);
});

test('warm cache reuses exact independent judgments; changed source keeps task answer but changes composition identity', async t => {
  const root = await fixture(t), cold = provider();
  const first = await run(root, cold, ['--task=contract.md', '--incremental']);
  assert.equal(first.code, 0); assert.equal(cold.requests.length, 4);
  const warm = provider(), second = await run(root, warm, ['--task=contract.md', '--incremental']);
  assert.equal(second.code, 0); assert.equal(warm.requests.length, 0);
  assert.equal(second.report.model_resolution.cached_answers, 4);
  assert.equal(second.report.model_resolution.verification, 'cached-answers-unverified');
  assert.equal(second.report.potential_profundity.review.reused, true);
  await writeFile(join(root, 'unit.bend'), source.replace('add(x,1)', 'add(x,2)'));
  const changed = provider(), third = await run(root, changed, ['--task=contract.md', '--incremental']);
  assert.equal(third.code, 0); assert.equal(changed.requests.length, 3);
  assert.ok(changed.requests.every(r => !r.questions.potential_profundity));
  assert.notEqual(first.report.composition.review.request_sha256, third.report.composition.review.request_sha256);
});

test('explicit v4 receipt reuse preserves both extra judgments and validates changed task input', async t => {
  const root = await fixture(t), p = provider();
  await run(root, p, ['--task=contract.md', '--output=first.json']);
  const replay = provider(), second = await run(root, replay, ['--task=contract.md', '--reuse=first.json']);
  assert.equal(second.code, 0); assert.equal(replay.requests.length, 0);
  await writeFile(join(root, 'contract.md'), contract + ' Also retain an explicit algebraic witness.');
  const changed = provider(), third = await run(root, changed, ['--task=contract.md', '--reuse=first.json']);
  assert.equal(third.code, 0); assert.equal(changed.requests.length, 4);
});

test('task or collaborator edits during review prevent qualification and cache publication', async t => {
  const root = await fixture(t), p = provider({ hook: async ({ phase }) => {
    if (phase === 'potential') await writeFile(join(root, 'contract.md'), contract + ' changed');
  } });
  const { report, code } = await run(root, p, ['--task=contract.md', '--incremental']);
  assert.equal(code, 3); assert.ok(report.source_freshness.changed_sources.includes('contract.md'));
  assert.equal(report.incremental_cache.persistence, 'source-stale');
  assert.equal(report.potential_profundity.review.cache.written, 0);
});

test('provider failure and model mismatch stop further phases and retain request identity', async t => {
  const root = await fixture(t), malformed = provider({ hook: ({ body, phase }) => {
    if (phase === 'potential') delete body.answers.potential_profundity;
  } });
  const first = await run(root, malformed, ['--task=contract.md']);
  assert.equal(first.code, 1); assert.equal(malformed.requests.length, 1);
  assert.ok(first.report.potential_profundity.review.request_sha256);
  const drift = provider({ hook: ({ body, phase }) => { if (phase === 'composition') body.model = 'different'; } });
  const second = await run(root, drift, ['--task=contract.md']);
  assert.equal(second.code, 1); assert.equal(drift.requests.length, 2);
  assert.equal(second.report.qualification.fully_qualified, false);
});

test('project inventory never substitutes an implicit whole-project composition claim', async t => {
  const root = await fixture(t);
  execFileSync('git', ['init', '--quiet'], { cwd: root });
  const p = provider({ potential: 0 }), result = await run(root, p, ['--task=contract.md', '--all'], []);
  assert.equal(result.code, 0);
  assert.equal(result.report.composition.available, false);
  assert.deepEqual(result.report.composition.reasons, ['explicit_selected_group_required']);
  assert.equal(result.report.qualification.fully_qualified, true);
  assert.equal(result.report.qualification.composition_required, false);
});

test('configuration and score validation preserve criticality independence and exact uncertainty', () => {
  assert.throws(() => assessStyle([], { ...config, potential_profundity: { ...config.potential_profundity, relevance_level: 8 } }), /Potential profundity/);
  assert.throws(() => assessStyle([], { ...config, potential_profundity: { ...config.potential_profundity, style_target: config.style_targets[0] } }), /stricter/);
  assert.equal(assessPotentialProfundity(score(4, 5), config).status, 'high');
  assert.equal(assessPotentialProfundity(score(2, 5), config).status, 'low');
  assert.equal(assessPotentialProfundity(score(0, 5), config, { available: false }).status, 'unavailable');
});
