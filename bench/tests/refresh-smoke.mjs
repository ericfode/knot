import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { result } from './campaign-smoke.mjs';
import { compileObservation } from '../run.mjs';
import { measureWasm } from '../wasm-worker.mjs';
import { ROOT, LOCAL, fileHash, sourceHashes, harnessHashes, run } from '../lib/system.mjs';
import { receiptJSON } from '../lib/receipt.mjs';

const manifest = 'bench/fixtures/refresh/expectations.json';
const frozen = JSON.parse(readFileSync(path.join(ROOT, manifest), 'utf8'));
const manifestSha256 = fileHash(path.join(ROOT, manifest));
assert.equal(frozen.status, 'frozen');
assert.equal(frozen.cases.length, 24);
assert.equal(new Set(frozen.cases.map(c => c.name)).size, 24);
assert.deepEqual(frozen.seed, result.environment.tools.seed);
for (const family of ['peano', 'cells', 'inline', 'wide']) {
  assert.equal(frozen.cases.filter(c => c.family === family).length, 6);
}

const directory = path.join(LOCAL, 'refresh');
mkdirSync(directory, { recursive: true });
const artifacts = mkdtempSync(path.join(directory, 'run-'));
const cases = [];
for (const c of frozen.cases) {
  assert.equal(fileHash(path.join(ROOT, c.program)), c.sourceSha256);
  assert.equal(c.seedCheck.exit, 0);
  assert.equal(c.seedCheck.stdout, 'All terms check.');
  for (const seed of Object.values(c.seed)) {
    assert.equal(seed.build.exit, 0);
    assert.equal(seed.observed.exit, 0);
    assert.ok(seed.observed.stdout.endsWith(`.${c.constructor}{}`));
  }
  const lanes = {};
  for (const lane of ['native', 'bun']) {
    const compiler = c.profile === 'knot-enum-1' ? result.builds[lane] : result.profileBuilds[c.profile][lane];
    const compiled = compileObservation(c, compiler, path.join(artifacts, `${c.name}-${lane}.wasm`));
    assert.equal(compiled.classification, 'Success', `${c.name}/${lane}: ${compiled.stderr}`);
    const evaluation = run([...result.evaluatorBuilds[lane].command, path.join(ROOT, c.program), 'main', 1048576]);
    assert.match(evaluation.stdout, new RegExp(`^Evaluated\\t\\d+\\t${c.expected}\\t${c.constructor}\\{\\}$`));
    const runtime = await measureWasm({ modules: [compiled.path], entry: 'main', args: [],
      expected: c.expected, profile: c.profile, warmup: 2, iterations: 4, repeat: 1, minSampleMs: 10 });
    assert.equal(runtime.result, c.expected);
    assert.equal(runtime.batches.length, 1);
    assert.ok(runtime.batches[0].elapsedNs >= 10000000);
    lanes[lane] = { compiled, evaluation, runtime };
  }
  assert.equal(lanes.native.runtime.verified[0].sha256, lanes.bun.runtime.verified[0].sha256);
  assert.equal(lanes.native.evaluation.stdout, lanes.bun.evaluation.stdout);
  cases.push({ name: c.name, family: c.family, size: c.size, sourceSha256: c.sourceSha256,
    expected: c.expected, constructor: c.constructor, profile: c.profile, lanes });
}
assert.equal(fileHash(path.join(ROOT, manifest)), manifestSha256);
assert.ok(frozen.cases.every(c => fileHash(path.join(ROOT, c.program)) === c.sourceSha256));
assert.deepEqual(sourceHashes(), result.environment.sourceHashes);
assert.deepEqual(harnessHashes(), result.environment.harnessHashes);
assert.equal(run(['git', 'rev-parse', 'HEAD']).stdout, result.environment.git.commit);

writeFileSync(path.join(ROOT, 'bench/receipts/refresh-edges.json'), receiptJSON({
  schemaVersion: 1, status: 'passed', command: 'npm run bench:verify', manifest, manifestSha256,
  seed: frozen.seed, sourceHashes: result.environment.sourceHashes, harnessHashes: result.environment.harnessHashes,
  counts: { programs: 24, frozenSeedChecks: 24, frozenSeedExecutions: 48, compilerLanes: 2,
    compilerObservations: 48, evaluatorObservations: 48, wasmBatches: 48, byteIdenticalPairs: 24 },
  note: 'Concrete differential correctness controls. These batches do not establish a performance comparison.', cases,
}));
console.log('Refresh edge gate passed: 24 new seed-frozen programs, 48 compiler/evaluator/Wasm observations, 24 byte-identical lane pairs.');
