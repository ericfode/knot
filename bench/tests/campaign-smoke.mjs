import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { benchmark, compileObservation } from '../run.mjs';
import { validateResult } from '../lib/compare.mjs';
import { ROOT, LOCAL, SEED_COMMAND, run, observe, fileHash } from '../lib/system.mjs';
import { runtimePrograms } from '../generate.mjs';

const { result, output } = benchmark({ suite: 'hillclimb', repeat: 1 });
validateResult(result);
assert.equal(result.cases.length, 201);
const generators = result.cases.filter(c => c.oracle.seed);
assert.equal(generators.length, 12);
assert.ok(generators.every(c => c.status === 'measured'));
let batches = 0;
for (const c of result.cases.filter(c => c.status === 'measured')) {
  for (const lane of Object.values(c.lanes)) {
    for (const batch of lane.batches ?? []) { assert.ok(batch.elapsedNs >= 10000000); batches++; }
  }
}

const mutations = [
  { family: 'peano', name: 'odd-base', from: 'case Zero{}: On{}', to: 'case Zero{}: Off{}' },
  { family: 'cells', name: 'ignore-cell', from: 'last(tail,head)', to: 'last(tail,value)' },
  { family: 'wide', name: 'wrong-arm', from: 'case T30{}: T31{}', to: 'case T30{}: T0{}' },
  { family: 'inline', name: 'omit-flip', from: 'step0(flip(x))', to: 'step0(x)' },
];
const directory = path.join(LOCAL, 'mutants', result.id); mkdirSync(directory, { recursive: true });
const mutants = [];
for (const mutation of mutations) {
  const original = runtimePrograms().find(p => p.family === mutation.family && p.size === 32);
  assert.equal(original.source.split(mutation.from).length, 2);
  const source = original.source.replace(mutation.from, mutation.to);
  const program = path.join(directory, `${mutation.name}.bend`); writeFileSync(program, source);
  const seed = run([...SEED_COMMAND, program, '--check-only']);
  assert.equal(seed.stdout, 'All terms check.');
  const reference = run([...SEED_COMMAND, program]);
  assert.notEqual(reference.stdout, `${original.constructor}{}`);
  const c = { ...original, program: path.relative(ROOT, program), compileBudgets: [] };
  const lanes = [];
  for (const lane of ['native', 'bun']) {
    const compiler = original.profile === 'knot-enum-1' ? result.builds[lane] : result.profileBuilds[original.profile][lane];
    const compiled = compileObservation(c, compiler, path.join(directory, `${mutation.name}-${lane}.wasm`));
    assert.equal(compiled.classification, 'Success');
    const evaluated = run([...result.evaluatorBuilds[lane].command, program, 'main', 1048576]);
    assert.match(evaluated.stdout, /Evaluated\t\d+\t0\t(?:Off|T0)\{\}/);
    const request = path.join(directory, `${mutation.name}-${lane}.json`);
    writeFileSync(request, JSON.stringify({ modules: [compiled.path], entry: 'main', args: [], expected: original.expected,
      profile: original.profile, warmup: 1, iterations: 1, repeat: 1 }));
    const killed = observe([process.execPath, path.join(ROOT, 'bench/wasm-worker.mjs'), request]);
    assert.equal(killed.exit, 1);
    const failure = JSON.parse(killed.stderr);
    assert.equal(failure.outcome.classification, 'InternalFailure');
    assert.equal(failure.outcome.code, 'wrong-result');
    lanes.push({ lane, compiled: compiled.classification, evaluator: evaluated.stdout, guard: failure });
  }
  mutants.push({ name: mutation.name, family: mutation.family, sourceSha256: fileHash(program), expected: original.expected,
    seedCheck: seed.stdout, seedResult: reference.stdout, lanes });
}
const receipts = path.join(ROOT, 'bench/receipts'); mkdirSync(receipts, { recursive: true });
const receipt = { schemaVersion: 1, status: 'passed', command: 'npm run bench:verify',
  sourceHashes: result.environment.sourceHashes, harnessHashes: result.environment.harnessHashes,
  seed: result.environment.tools.seed, fixturePrograms: 189, generators: 12, compilerLanes: 2,
  coverage: result.coverage, runtimeBatches: batches, minimumBatchMs: 10, mutants,
  resultSha256: fileHash(output),
  classifications: result.cases.map(c => ({ name: c.name, sourceSha256: c.sourceSha256, status: c.status,
    classification: c.classification ?? 'Success', phase: c.probes.native.phase, code: c.probes.native.code,
    d4Discrepancy: c.d4Discrepancy ?? false,
    runtime: c.status === 'measured' ? c.lanes.native.runtimeStatus ?? 'measured' : undefined })) };
writeFileSync(path.join(receipts, 'verification.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(`Campaign benchmark gate passed: 189 fixture programs, 12 generators, ${result.coverage.measured} measured programs, ${batches} runtime batches >=10 ms, 4 seed-type-correct mutants killed in both lanes.`);
