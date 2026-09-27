import test from 'node:test';
import assert from 'node:assert/strict';
import { median, summarize, compareSamples } from '../lib/stats.mjs';

test('median, unscaled MAD and min retain outliers without mutating inputs', () => {
  const samples = [100, 4, 1, 2, 3];
  assert.deepEqual(summarize(samples), { n: 5, median: 3, mad: 1, min: 1 });
  assert.equal(median([10, 2, 8, 4]), 6);
  assert.deepEqual(samples, [100, 4, 1, 2, 3]);
});

test('bootstrap is deterministic and has the candidate/baseline direction', () => {
  const options = { seed: 17, resamples: 2000 };
  const a = compareSamples([98, 100, 102, 99, 101], [49, 50, 51, 49.5, 50.5], options);
  assert.deepEqual(a, compareSamples([98, 100, 102, 99, 101], [49, 50, 51, 49.5, 50.5], options));
  assert.equal(a.ratio, 0.5);
  assert.equal(a.verdict, 'faster');
  assert.ok(a.ci[0] > 0.47 && a.ci[1] < 0.53 && a.ci[0] < a.ci[1]);
  assert.equal(compareSamples([50, 50, 50], [100, 100, 100]).verdict, 'slower');
});

test('strict practical margin is required, even with zero sample variance', () => {
  const base = [100, 100, 100];
  assert.equal(compareSamples(base, [99, 99, 99]).verdict, 'no change');
  assert.equal(compareSamples(base, [99, 99, 99], { margin: 0 }).verdict, 'faster');
  assert.equal(compareSamples(base, [98, 98, 98]).verdict, 'no change');
  assert.equal(compareSamples(base, [102, 102, 102]).verdict, 'no change');
  assert.deepEqual(compareSamples(base, base).ci, [1, 1]);
});

test('uncertain medians do not establish a speedup', () => {
  const result = compareSamples([10, 50, 100, 150, 200], [9, 40, 90, 140, 210]);
  assert.equal(result.verdict, 'no change');
  assert.ok(result.ci[0] < 1 && result.ci[1] > 1);
});

test('too few observations cannot manufacture confidence', () => {
  const result = compareSamples([100], [1]);
  assert.equal(result.verdict, 'insufficient samples');
  assert.equal(result.ci, null);
});

test('reject empty, nonfinite, nonpositive samples and invalid comparison settings', () => {
  for (const samples of [[], [NaN], [Infinity], [undefined]]) assert.throws(() => summarize(samples));
  for (const samples of [[0, 1, 2], [-1, 1, 2]]) assert.throws(() => compareSamples(samples, [1, 2, 3]));
  for (const options of [{ margin: -1 }, { margin: 1 }, { confidence: 1 }, { confidence: 0 },
    { resamples: 0 }, { resamples: 100.5 }, { seed: -1 }, { seed: NaN }]) {
    assert.throws(() => compareSamples([1, 2, 3], [1, 2, 3], options));
  }
});
