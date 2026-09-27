import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { compareStyleBaseline } from '../scripts/perch-style-campaign.mjs';

const currentConfig = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url)));
const config = structuredClone(currentConfig);
config.version = 3;
config.criticality.style_target = config.potential_profundity.style_target;
delete config.potential_profundity;
const identity = { rubric_sha256: 'rubric', parser: 'parser' };
const specimen = target => ({ target, path: target.split('::')[0], kind: 'bend_definition', line: 1,
  source_sha256: 'source', state_sha256: 'state', context: { truncated: false, files: [] },
  model: 'model', answers: { ...Object.fromEntries([...config.dimensions, ...config.diagnostic_dimensions].map(d => [d.id,
    { probabilities: Object.fromEntries(d.levels.map((_, i) => [i, i === 3 ? 1 : 0])), score: 3, confidence: 1 }])),
    criticality: { probabilities: { 0: 1, 1: 0 }, score: 0, confidence: 1 } } });
const baseline = rows => ({ schema: 2, command: 'style-rank', ...identity, rows, assessments: [], requested_model: 'requested' });
const inventory = { discovered_files: ['src/a.bend', 'src/new.bend', 'tests/broken.bend', 'tests/empty.bend'],
  unranked: [{ path: 'tests/broken.bend', reason: 'expected parser rejection' }], empty_files: ['tests/empty.bend'] };

test('campaign retains unrated, stale-helper, missing and unparseable coverage instead of inheriting a pass', () => {
  const original = specimen('src/a.bend::a');
  const vanished = specimen('src/a.bend::removed');
  const stale = { ...original, state_sha256: 'changed-helper' };
  const fresh = specimen('src/new.bend::new');
  const result = compareStyleBaseline([stale, fresh], inventory, baseline([original, vanished]), config, identity);
  assert.deepEqual(result.units.map(u => u.baseline_status), ['stale', 'unrated']);
  assert.equal(result.summary.matches_all_three_baseline_targets, 0);
  assert.deepEqual(result.no_longer_parsed_targets, [vanished.target]);
  assert.equal(result.summary.unranked_files, 1);
  assert.deepEqual(result.inventory.empty_files, ['tests/empty.bend']);
});

test('only matching source, context, parser and rubric can carry a baseline target result', () => {
  const unit = specimen('src/a.bend::a');
  const same = compareStyleBaseline([unit], inventory, baseline([unit]), config, identity);
  assert.equal(same.summary.matches_all_three_baseline_targets, 1);
  for (const changed of [{ ...unit, source_sha256: 'new' }, { ...unit, context: { truncated: true } }]) {
    assert.equal(compareStyleBaseline([changed], inventory, baseline([unit]), config, identity).summary.matches, 0);
  }
  for (const field of ['parser', 'rubric_sha256']) {
    const changed = { ...identity, [field]: 'new' };
    assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, changed).summary.matches, 0);
  }
});

test('failed or empty baselines cannot make a campaign look covered', () => {
  const unit = specimen('src/a.bend::a');
  for (const prior of [{ ...baseline([unit]), failure: 'provider unavailable' }, baseline([])]) {
    assert.throws(() => compareStyleBaseline([unit], inventory, prior, config, identity), /nonempty style baseline/);
  }
});

test('a matching critical baseline still needs Galaxy brain under the historical v3 policy', () => {
  const unit = specimen('src/a.bend::a');
  unit.answers.criticality = { probabilities: { 0: 0, 1: 1 }, score: 1, confidence: 1 };
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_three_baseline_targets, 0);
  unit.answers.maximally_big_brain = { probabilities: { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 1 }, score: 5, confidence: 1 };
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_three_baseline_targets, 1);
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_required_baseline_targets, 1);
  unit.answers.payoff = { probabilities: { 0: 0, 1: 0, 2: 1, 3: 0, 4: 0 }, score: 2, confidence: 1 };
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_required_baseline_targets, 0);
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_three_baseline_targets, 0);
  delete unit.answers.payoff;
  assert.throws(() => compareStyleBaseline([unit], inventory, baseline([unit]), config, identity), /Invalid Score answer/);
  unit.context.truncated = true;
  assert.equal(compareStyleBaseline([unit], inventory, baseline([unit]), config, identity).summary.matches_all_required_baseline_targets, 0);
});

test('v4 matching declaration ratings do not establish task or composition qualification', () => {
  const unit = specimen('src/a.bend::a');
  unit.answers.criticality = { probabilities: { 0: 0, 1: 1 }, score: 1, confidence: 1 };
  const result = compareStyleBaseline([unit], inventory, baseline([unit]), currentConfig, identity);
  assert.equal(result.units[0].baseline_status, 'matches');
  assert.equal(result.units[0].matches_declaration_baseline_targets, true);
  assert.equal(result.units[0].run_requirements_status, 'requires_task_and_composition_review');
  assert.equal(result.summary.matches_all_required_baseline_targets, 0);
  assert.equal(result.summary.matches_all_three_baseline_targets, 0);
});
