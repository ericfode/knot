import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { benchmark } from '../run.mjs';
import { compareResults, validateResult } from '../lib/compare.mjs';

// Intentionally separate from *.test.mjs: pure statistics/comparison tests do
// not build a compiler. bench:verify also requires this real two-lane gate.
const { result, output } = benchmark({ suite: 'smoke' });
assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')), result);
validateResult(result);
for (const lane of ['native', 'bun']) {
  const data = result.cases[0].lanes[lane];
  assert.equal(data.compile.n, 3);
  assert.equal(data.runtime.n, 3);
  assert.equal(data.correctness.result, 1);
  assert.ok(data.compilations.every(c => existsSync(c.path)));
}
const comparison = compareResults(result, result, { resamples: 200 });
assert.equal(comparison.regression, false);
assert.equal(comparison.insufficient, false);
console.log('Smoke passed: both compiler lanes, validated artifacts, warm repeated calls, JSON round trip and comparison.');

await import('./campaign-smoke.mjs');
await import('./refresh-smoke.mjs');
