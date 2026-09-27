import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { metric } from '../lib/stats.mjs';
import { compareResults, formatComparison } from '../lib/compare.mjs';
import { ROOT } from '../lib/system.mjs';

const options = { resamples: 200 };
function result({ compile = 10, runtime = 20, size = 68, build = 100, repeat = 3 } = {}) {
  const values = x => Array(repeat).fill(x);
  const lane = () => ({ compile: metric('ms', values(compile)), runtime: metric('ns/call', values(runtime)),
    size: metric('bytes', values(size)),
    correctness: { valid: true, result: 1, checkedCalls: repeat + 1 + 20 + repeat * 100 },
    compilations: Array.from({ length: repeat + 1 }, (_, i) => ({ ms: compile, bytes: size, sha256: '0'.repeat(64), valid: true, result: 1, warmup: i === 0 })) });
  const compiler = () => ({ metric: metric('ms', [build]), artifacts: [{ ms: build, correctness: { valid: true, result: 1 } }] });
  return { schemaVersion: 1, status: 'passed',
    environment: { machine: { cpuModel: 'test cpu' }, tools: { node: 'test node' }, controls: {},
      sourceHashes: { 'src/wasm.bend': 'base' }, harnessHashes: { 'bench/run.mjs': 'harness' }, git: { commit: 'base', dirty: false } },
    suite: { name: 'smoke', sha256: 'suite', caseCount: 1 },
    protocol: { version: 1, lanes: ['native', 'bun'], compileWarmup: 1, buildRepeat: 1, runtime: { warmup: 20, iterations: 100 } },
    builds: { native: compiler(), bun: compiler() },
    cases: [{ name: 'flag', program: 'tests/subsets/s1/flag.bend', sourceSha256: 'flag', entry: 'flip', args: [0],
      expected: 1, oracle: { kind: 'literal' }, repeat, lanes: { native: lane(), bun: lane() } }] };
}

test('separate metrics expose a regression even when another metric improves', () => {
  const comparison = compareResults(result(), result({ compile: 5, runtime: 30 }), options);
  assert.equal(comparison.regression, true);
  assert.equal(comparison.rows.find(r => r.metric === 'compile').verdict, 'faster');
  assert.equal(comparison.rows.find(r => r.metric === 'runtime').verdict, 'slower');
  assert.match(formatComparison(comparison), /ms/);
  assert.match(formatComparison(comparison), /ns\/call/);
});

test('size regressions are explicit and builds are informational by default', () => {
  assert.equal(compareResults(result(), result({ build: 10000 }), options).regression, false);
  assert.equal(compareResults(result(), result({ build: 10000 }), { ...options, includeBuild: true }).insufficient, true);
  const comparison = compareResults(result(), result({ size: 90 }), options);
  assert.equal(comparison.regression, true);
  assert.equal(comparison.rows.find(r => r.metric === 'size').verdict, 'larger');
});

test('different source revisions are the intended comparison, not an incompatibility', () => {
  const candidate = result({ compile: 5 });
  candidate.environment.git = { commit: 'candidate', dirty: true };
  candidate.environment.sourceHashes['src/wasm.bend'] = 'candidate';
  assert.equal(compareResults(result(), candidate, options).regression, false);
});

test('repetition counts may differ, but both need at least three target samples', () => {
  assert.equal(compareResults(result(), result({ repeat: 5 }), options).insufficient, false);
  assert.equal(compareResults(result(), result({ repeat: 1 }), options).insufficient, true);
});

test('cached summary fields are recomputed from raw samples', () => {
  const candidate = result({ runtime: 40 });
  candidate.cases[0].lanes.native.runtime.median = 0.1;
  assert.equal(compareResults(result(), candidate, options).regression, true);
});

test('incomplete, incorrect, incompatible and mismatched-coverage records fail closed', async t => {
  const changes = {
    schema: x => { x.schemaVersion = 2; },
    failed: x => { x.status = 'failed'; },
    missingCase: x => { x.cases = []; },
    missingLane: x => { delete x.cases[0].lanes.bun; },
    missingBuild: x => { delete x.builds.native; },
    wrongBuild: x => { x.builds.native.artifacts[0].correctness.result = 0; },
    wrongResult: x => { x.cases[0].lanes.native.correctness.result = 0; },
    wrongSample: x => { x.cases[0].lanes.native.compilations[1].result = 0; },
    skippedCall: x => { x.cases[0].lanes.native.correctness.checkedCalls--; },
    modifiedTime: x => { x.cases[0].lanes.native.compile.samples[0] = 1; },
    invalidTime: x => { x.cases[0].lanes.native.runtime.samples[0] = null; },
    unit: x => { x.cases[0].lanes.native.runtime.unit = 'ms'; },
    cpu: x => { x.environment.machine.cpuModel = 'another cpu'; },
    node: x => { x.environment.tools.node = 'another node'; },
    harness: x => { x.environment.harnessHashes['bench/run.mjs'] = 'changed'; },
    protocol: x => { x.protocol.compile = 'another timer'; },
    fixture: x => { x.cases[0].sourceSha256 = 'changed'; },
    argument: x => { x.cases[0].args = [1]; },
    suite: x => { x.suite.sha256 = 'changed'; },
    oracle: x => { x.cases[0].oracle.kind = 'evaluator'; },
  };
  for (const [name, change] of Object.entries(changes)) await t.test(name, () => {
    const candidate = result();
    change(candidate);
    assert.throws(() => compareResults(result(), candidate, options));
  });
});

test('CLI returns 0 for no regression, 1 for regression, 2 for unusable evidence', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'knot-bench-compare-'));
  try {
    const base = path.join(dir, 'base.json'), next = path.join(dir, 'next.json');
    writeFileSync(base, JSON.stringify(result()));
    for (const [candidate, status] of [[result(), 0], [result({ runtime: 40 }), 1], [result({ repeat: 1 }), 2], [{ ...result(), status: 'failed' }, 2]]) {
      writeFileSync(next, JSON.stringify(candidate));
      const ran = spawnSync(process.execPath, [path.join(ROOT, 'bench/compare.mjs'), base, next, '--resamples=200'], { encoding: 'utf8' });
      assert.equal(ran.status, status, ran.stderr);
    }
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
