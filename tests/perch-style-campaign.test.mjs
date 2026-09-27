import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { compareStyleBaseline } from '../scripts/perch-style-campaign.mjs';

const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url)));
const identity = { rubric_sha256: 'rubric', parser: 'parser' };
const specimen = target => ({ target, path: target.split('::')[0], kind: 'bend_definition', line: 1,
  source_sha256: 'source', state_sha256: 'state', context: { truncated: false, files: [] },
  model: 'model', answers: Object.fromEntries(config.dimensions.map(d => [d.id,
    { probabilities: { 0: 0, 1: 0, 2: 0, 3: 1, 4: 0 }, score: 3, confidence: 1 }])) });
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
