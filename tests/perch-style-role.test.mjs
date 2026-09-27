import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as style from '../scripts/perch-style.mjs';

const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
// Existing v4 fixture, unchanged; these tests vary judgments, not its behavior.
const source = 'import Base\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: helper(x)\n';
const scaled = ['highly_memetic', 'anticipation', 'payoff'];
const score = (value, count) => ({ type: 'score', score: value, confidence: 1,
  probabilities: Object.fromEntries(Array.from({ length: count }, (_, i) => [i, i === value ? 1 : 0])) });
const roleScore = probabilityLeading => ({ type: 'score', score: probabilityLeading, confidence: 0.8,
  probabilities: { 0: 1 - probabilityLeading, 1: probabilityLeading } });

function row(role = 0, criticality = 1, truncated = false) {
  return { target: 'unit.bend::helper', kind: 'bend_definition', context: { truncated, unresolved: [], files: [] },
    answers: { ...Object.fromEntries([...config.dimensions, ...config.diagnostic_dimensions].map(d =>
      [d.id, score(scaled.includes(d.id) ? 2 : 3, d.levels.length)])), criticality: score(criticality, 2), style_role: roleScore(role) } };
}

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'perch-style-role-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  await writeFile(join(root, 'unit.bend'), source);
  return root;
}

function provider({ role = 0, potential = 0, family = 3, galaxy = 5, contribution = 2 } = {}) {
  const requests = [];
  return { requests, fetchImpl: async (_url, options) => {
    const request = JSON.parse(options.body);
    requests.push(request);
    const composition = Array.isArray(request.state.files);
    const answers = Object.fromEntries(Object.entries(request.questions).map(([id, question]) => [id,
      id === 'style_role' ? roleScore(role) : id === 'criticality' ? score(1, 2)
        : id === 'potential_profundity' ? score(potential, question.criteria.length)
          : score(composition ? id === 'maximally_big_brain' ? galaxy : family
            : scaled.includes(id) ? contribution : 3, question.criteria.length)]));
    return { ok: true, json: async () => ({ model: 'jev-1.13.0', answers, usage: { input_tokens: 10, output_tokens: 2 } }) };
  } };
}

async function run(root, p, options = [], targets = ['unit.bend']) {
  const output = [];
  const code = await style.runStyleRanking(['--live', '--json', ...options, ...targets], { root,
    env: { PERCH_API_KEY: 'mock-only', PERCH_MODEL_ID: 'jev-1.13.0' }, fetchImpl: p.fetchImpl,
    stdout: text => output.push(text), stderr: () => {} });
  return { code, report: JSON.parse(output[0]) };
}

test('supporting roles scale only three axes, independently of criticality', () => {
  for (const criticality of [0, 1]) {
    const unit = row(0, criticality);
    assert.equal(style.assessStyleRole(unit, config).status, 'supporting');
    const assessments = style.assessStyle([unit], config);
    for (const assessment of assessments) {
      assert.equal(assessment.target_level, scaled.includes(assessment.dimension) ? 2 : 3);
      if (scaled.includes(assessment.dimension)) {
        assert.equal(assessment.style_role, 'supporting');
        assert.equal(assessment.target_basis, 'supporting_role');
      }
    }
  }
});

test('leading and uncertain roles keep level3; truncation cannot establish a supporting exemption', () => {
  for (const [probability, expected] of [[1, 'leading'], [.6, 'leading'], [.5, 'uncertain']]) {
    const unit = row(probability);
    assert.equal(style.assessStyleRole(unit, config).status, expected);
    const assessments = style.assessStyle([unit], config).filter(a => scaled.includes(a.dimension));
    assert.ok(assessments.every(a => a.target_level === 3 && a.target_basis === `${expected}_role` && a.style_role === expected));
    assert.ok(assessments.every(a => a.status === 'below_target'));
  }
  assert.equal(style.assessStyleRole(row(.4), config).status, 'supporting');
  assert.equal(style.assessStyleRole(row(0, 1, true), config).status, 'uncertain');
  const absentContext = row();
  delete absentContext.context;
  assert.equal(style.assessStyleRole(absentContext, config).status, 'uncertain');
  const referenceContext = row();
  referenceContext.context.unresolved = [{ reason: 'unresolved-or-builtin', name: 'U32.add' }];
  assert.equal(style.assessStyleRole(referenceContext, config).status, 'supporting');
  referenceContext.context.unresolved = [{ reason: 'unresolved-or-builtin', name: 'missingCollaborator' }];
  assert.equal(style.assessStyleRole(referenceContext, config).status, 'uncertain');
  const missing = row();
  delete missing.answers.style_role;
  assert.throws(() => style.assessStyleRole(missing, config));
});

test('a helper named helper can be leading; public names do not override the classifier', () => {
  assert.equal(style.assessStyleRole(row(1), config).status, 'leading');
  const publicAdapter = { ...row(0), target: 'unit.bend::main' };
  assert.equal(style.assessStyleRole(publicAdapter, config).status, 'supporting');
});

test('missing task keeps potential advisory but always requires whole-composition three-axis evidence', async t => {
  const root = await fixture(t), p = provider();
  const { report, code } = await run(root, p);
  assert.equal(code, 0);
  assert.equal(report.potential_profundity.assessment.status, 'unavailable');
  assert.equal(report.composition.required, true);
  assert.equal(report.composition.galaxy_required, false);
  assert.deepEqual(report.composition.assessment.assessments.map(a => a.dimension).sort(), [...scaled].sort());
  assert.ok(report.composition.assessment.assessments.every(a => a.target_level === 3 && a.status === 'meets_target'));
  assert.equal(report.style_role.assessments.length, 2);
  assert.ok(report.style_role.assessments.every(a => a.status === 'supporting'));
  const familyRequests = p.requests.filter(r => Array.isArray(r.state.files));
  assert.equal(familyRequests.length, 1);
  assert.deepEqual(Object.keys(familyRequests[0].questions).sort(), [...scaled].sort());
  assert.equal('style_role' in familyRequests[0].state, false);
  assert.equal('answers' in familyRequests[0].state, false);
});

test('composition questions keep the generic form unless per-axis composition wording is configured', async t => {
  const plain = await fixture(t), p = provider();
  await run(plain, p);
  const generic = p.requests.find(request => Array.isArray(request.state.files));
  for (const id of scaled) {
    const title = [...config.dimensions, ...config.diagnostic_dimensions].find(d => d.id === id).title;
    assert.equal(generic.questions[id].instructions,
      `${config.style_role.composition_instructions} Apply the ${title} levels below to the entire mechanism as a leading expression.`);
  }
  const worded = await fixture(t), q = provider();
  const custom = structuredClone(config);
  custom.style_role.composition_axis_instructions = { anticipation: 'Stated laws announce what the mechanism will do.' };
  await writeFile(join(worded, 'perch-style.json'), JSON.stringify(custom));
  await run(worded, q);
  const questions = q.requests.find(request => Array.isArray(request.state.files)).questions;
  assert.match(questions.anticipation.instructions, / Stated laws announce what the mechanism will do\. Apply the /);
  assert.equal(questions.payoff.instructions, generic.questions.payoff.instructions);
  const invalid = structuredClone(config);
  invalid.style_role.composition_axis_instructions = { maximally_big_brain: 'not a scaled axis' };
  assert.throws(() => style.assessStyle([], invalid), /Composition axis instructions/);
});

test('all-support declaration success cannot bypass a weak whole composition', async t => {
  const root = await fixture(t), p = provider({ family: 2 });
  const { report, code } = await run(root, p);
  assert.equal(report.style_summary.meets_all, 2);
  assert.equal(report.composition.assessment.status, 'below_target');
  assert.equal(report.qualification.fully_qualified, false);
  assert.equal(code, 3);
});

test('low potential still grades composition; high potential adds only the Galaxy question', async t => {
  const root = await fixture(t);
  for (const [potential, expectedCount] of [[0, 3], [4, 4]]) {
    const p = provider({ potential }), { report, code } = await run(root, p, ['--cohort=Return the unsigned successor.']);
    assert.equal(code, 0);
    assert.ok(p.requests[0].questions.potential_profundity);
    assert.equal(report.composition.required, true);
    assert.equal(report.composition.galaxy_required, potential === 4);
    assert.equal(report.composition.assessment.assessments.length, expectedCount);
    assert.ok(report.assessments.filter(a => a.dimension === 'maximally_big_brain').every(a => a.target_level === 3));
  }
  const high = await run(root, provider({ potential: 4, galaxy: 4 }), ['--cohort=Return the unsigned successor.']);
  assert.equal(high.code, 3);
  assert.equal(high.report.composition.assessment.assessments.find(a => a.dimension === 'maximally_big_brain').target_level, 5);
});

test('whole-project inventory remains explicit attention without a bounded composition group', async t => {
  const root = await fixture(t);
  execFileSync('git', ['init', '--quiet'], { cwd: root });
  const { report, code } = await run(root, provider(), ['--all'], []);
  assert.equal(code, 3);
  assert.equal(report.coverage.ranked, 2);
  assert.equal(report.composition.required, true);
  assert.equal(report.composition.available, false);
  assert.equal(report.qualification.fully_qualified, false);
});

test('role and composition judgments reuse exact requests; contribution policy changes invalidate cache', async t => {
  const root = await fixture(t), first = provider();
  const cold = await run(root, first, ['--incremental']);
  assert.equal(cold.code, 0);
  assert.equal(first.requests.length, 3);
  assert.ok(first.requests.filter(r => !r.state.files).every(r => r.questions.style_role));
  const warm = provider(), cached = await run(root, warm, ['--incremental']);
  assert.equal(cached.code, 0);
  assert.equal(warm.requests.length, 0);
  assert.equal(cached.report.model_resolution.cached_answers, 3);
  const changed = structuredClone(config);
  changed.style_role.instructions += ' Preserve exact caller conventions.';
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(changed));
  const stale = provider(), revised = await run(root, stale, ['--incremental']);
  assert.equal(revised.code, 0);
  assert.equal(stale.requests.length, 3);
});
