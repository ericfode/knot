import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fixtureCases, FIXTURE_SUITES } from '../lib/fixtures.mjs';
import { loadSuite } from '../lib/suite.mjs';
import { runtimePrograms } from '../generate.mjs';
import { measureWasm, runtimeFailure } from '../wasm-worker.mjs';
import { outcome } from '../lib/outcome.mjs';
import { validateResult, compareResults } from '../lib/compare.mjs';
import { metric } from '../lib/stats.mjs';
import { compileObservation } from '../run.mjs';
import { observe, ROOT, LOCAL } from '../lib/system.mjs';

test('all six frozen suites retain positives, negatives and source identities', () => {
  assert.deepEqual(FIXTURE_SUITES.map(s => fixtureCases(s).length), [19, 8, 42, 40, 40, 40]);
  for (const suite of FIXTURE_SUITES) {
    const cases = fixtureCases(suite);
    assert.ok(cases.every(c => c.probe && c.profile === 'knot-fields-wasm-1' && c.oracle.manifestSha256.length === 64));
    assert.ok(cases.some(c => c.seedValid));
    if (suite !== 'fields-wasm') assert.ok(cases.some(c => !c.seedValid));
  }
  const all = loadSuite('hillclimb');
  assert.equal(all.cases.length, 201);
  assert.equal(new Set(all.cases.map(c => c.name)).size, 201);
  assert.equal(all.runtime.minSampleMs, 10);
  assert.equal(fixtureCases('recursion')[0].expected, null);
  assert.match(fixtureCases('recursion')[0].oracle.expectedObservation, /Results\{/);
  assert.equal(fixtureCases('recursion').find(c => c.name === 'recursion-second-descent').oracle.expectedObservation,
    'Evaluated\t0\t1\tSucc{Zero{}}');
});

test('new generators preserve the fixed formulas, sizes and deterministic source', () => {
  const a = runtimePrograms();
  assert.deepEqual(a, runtimePrograms());
  assert.equal(a.length, 12);
  assert.equal(new Set(a.map(p => p.program)).size, 12);
  for (const p of a) {
    assert.ok(p.source.length < 65536);
    assert.equal(p.expected, p.family === 'wide' ? p.size - 1 : 1);
    assert.equal(p.entry, 'main'); assert.deepEqual(p.args, []);
  }
  assert.match(a.find(p => p.name === 'peano-192').source, /parity\(q\)/);
  assert.match(a.find(p => p.name === 'cells-192').source, /last\(tail,head\)/);
  assert.match(a.find(p => p.name === 'inline-192').source, /step192\(On\{\}\)/);
});

test('failure classes preserve language, resource and process boundaries', () => {
  for (const [exit, classification] of [[2, 'Invalid'], [3, 'Unsupported'], [4, 'Exhausted'], [5, 'HostFailure'], [6, 'InternalFailure']]) {
    assert.deepEqual(outcome({ exit, stderr: `${classification}\tcheck\tcode\t1`, stdout: '' }), { classification, phase: 'check', code: 'code' });
  }
  assert.equal(outcome({ error: 'ETIMEDOUT' }).classification, 'Exhausted');
  assert.equal(outcome({ exit: 3, stderr: 'Invalid\tcheck\tcode' }).classification, 'HostFailure');
  assert.equal(outcome({ exit: null, signal: 'SIGSEGV' }).classification, 'HostFailure');
  assert.equal(outcome({ exit: 0 }).classification, 'Success');
  assert.deepEqual(runtimeFailure(new WebAssembly.RuntimeError('unreachable'), 'knot-fields-wasm-1'),
    { classification: 'Exhausted', phase: 'wasm', code: 'arena-overflow' });
  assert.equal(runtimeFailure(new WebAssembly.RuntimeError('unreachable'), 'knot-enum-1').classification, 'HostFailure');
  assert.equal(runtimeFailure(new RangeError('Maximum call stack size exceeded'), 'knot-enum-1').code, 'call-stack');
});

test('fields calls get fresh instances and every batch meets the duration floor', async () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'bench-fields-'));
  try {
    // Independent Wasm counter: ++global. A reused instance returns 2, then 3.
    const bytes = Buffer.from('0061736d010000000105016000017f030201000606017f0141000b070501016600000a0d010b00230041016a240023000b', 'hex');
    const file = path.join(dir, 'counter.wasm'); writeFileSync(file, bytes);
    const config = { modules: [file], entry: 'f', args: [], expected: 1, warmup: 2, iterations: 4, repeat: 3, minSampleMs: 10 };
    const r = await measureWasm({ ...config, profile: 'knot-fields-wasm-1' });
    assert.equal(r.lifecycle, 'fresh-instance-per-call');
    assert.ok(r.batches.every(b => b.elapsedNs >= 10000000 && b.calls % 4 === 0));
    assert.deepEqual(r.samples, r.batches.map(b => b.elapsedNs / b.calls));
    assert.equal(r.checkedCalls, 3 + r.batches.reduce((n, b) => n + b.calls, 0));
    await assert.rejects(measureWasm(config), /wrong result/);
    await assert.rejects(measureWasm({ ...config, profile: 'unknown' }), /unsupported Wasm profile/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('the guard checks a wrong measured call after successful validation and warmup', async () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'bench-guard-'));
  try {
    // ++global < 3: first two calls pass, the first timed call must fail.
    const bytes = Buffer.from('0061736d010000000105016000017f030201000606017f0141000b070501016600000a10010e00230041016a240023004103480b', 'hex');
    const file = path.join(dir, 'changes.wasm'); writeFileSync(file, bytes);
    await assert.rejects(measureWasm({ modules: [file], entry: 'f', args: [], expected: 1, warmup: 1, iterations: 1, repeat: 1 }),
      e => e.outcome?.classification === 'InternalFailure' && /wrong result/.test(e.message));
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

function evidence() {
  const build = () => ({ metric: metric('ms', [1]), artifacts: [{ ms: 1, correctness: { valid: true, result: 1 } }] });
  const probe = { exit: 0, stdout: 'Built\t68', stderr: '', classification: 'Success', path: 'output.wasm' };
  const evaluation = { exit: 0, stdout: 'Evaluated\t0\t1\tOn{}', ms: 1 };
  const lane = () => ({ compile: metric('ms', [1, 1, 1]), size: metric('bytes', [68, 68, 68]),
    compilations: Array.from({ length: 4 }, (_, i) => ({ ...probe, valid: true, result: 1, bytes: 68, ms: 1, warmup: i === 0, sha256: 'a'.repeat(64) })),
    runtime: metric('ns/call', [100000, 100000, 100000]), batches: Array.from({ length: 3 }, () => ({ calls: 100, elapsedNs: 10000000 })),
    lifecycle: 'fresh-instance-per-call', correctness: { valid: true, result: 1, checkedCalls: 305 },
    evaluation: { status: 'measured', classification: 'Success', metric: metric('ms', [1, 1, 1]), warmup: evaluation, observations: [evaluation, evaluation, evaluation] } });
  return { schemaVersion: 2, status: 'passed', environment: { machine: {}, tools: {}, sourceHashes: {}, harnessHashes: {}, git: {} },
    protocol: { version: 2, lanes: ['native', 'bun'], compileWarmup: 1, buildRepeat: 1, runtime: { warmup: 1, iterations: 100, minSampleMs: 10 }, selfCost: {} },
    suite: { name: 'test', caseCount: 1 }, builds: { native: build(), bun: build() }, profileBuilds: { 'knot-fields-wasm-1': { native: build(), bun: build() } },
    cases: [{ name: 'cells', program: 'cells.bend', sourceSha256: 's', profile: 'knot-fields-wasm-1', entry: 'main', args: [], expected: 1,
      seedValid: true, repeat: 3, runtimeEligible: true, oracle: { kind: 'literal', constructor: 'On' }, status: 'measured', probes: { native: probe, bun: probe },
      lanes: { native: lane(), bun: lane() } }], coverage: { measured: 1, notYetCompilable: 0, d4Discrepancies: 0 } };
}

test('version 2 comparison rejects missing duration, lifecycle, oracle and coverage evidence', async t => {
  validateResult(evidence());
  assert.equal(compareResults(evidence(), evidence(), { resamples: 100 }).regression, false);
  const changes = {
    duration: r => { r.cases[0].lanes.native.batches[0].elapsedNs = 1; },
    lifecycle: r => { r.cases[0].lanes.native.lifecycle = 'persistent-instance'; },
    calls: r => { r.cases[0].lanes.native.correctness.checkedCalls--; },
    evaluate: r => { r.cases[0].lanes.native.evaluation.observations[0].stdout = 'Evaluated\t0\t0\tOff{}'; },
    profileBuild: r => { delete r.profileBuilds['knot-fields-wasm-1']; },
    coverage: r => { r.coverage.measured++; },
    probe: r => { r.cases[0].probes.native.exit = 3; },
    samples: r => { r.cases[0].lanes.native.runtime.samples[0] = 1; },
  };
  for (const [name, mutate] of Object.entries(changes)) await t.test(name, () => {
    const r = evidence(); mutate(r); assert.throws(() => validateResult(r));
  });
});

test('unavailable capabilities retain classification and cannot masquerade as timing wins', () => {
  const r = evidence(), c = r.cases[0];
  c.status = 'not-yet-compilable'; c.classification = 'Unsupported'; c.d4Discrepancy = false; c.lanes = {};
  c.probes = Object.fromEntries(['native', 'bun'].map(lane => [lane, { exit: 3, stdout: '', stderr: 'Unsupported\tparse\timport' }]));
  r.coverage = { measured: 0, notYetCompilable: 1, d4Discrepancies: 0 };
  validateResult(r);
  assert.equal(compareResults(r, r, { resamples: 100 }).insufficient, true);
  assert.throws(() => compareResults(evidence(), r), /incompatible workloads/);
  c.classification = 'Invalid';
  for (const p of Object.values(c.probes)) { p.exit = 2; p.stderr = 'Invalid\tparse\tsyntax'; }
  assert.throws(() => validateResult(r), /invalid exclusion/);
  c.d4Discrepancy = true; r.coverage.d4Discrepancies = 1;
  validateResult(r);
});

test('runtime exhaustion preserves a failed observation and no runtime samples', () => {
  const r = evidence();
  for (const m of Object.values(r.cases[0].lanes)) {
    m.runtime = null;
    delete m.batches; delete m.correctness;
    m.runtimeStatus = { classification: 'Exhausted', phase: 'wasm', code: 'arena-overflow' };
    m.runtimeEvidence = { exit: 1, stderr: JSON.stringify({ outcome: m.runtimeStatus }) };
    for (const a of m.compilations) a.result = null;
  }
  validateResult(r);
  const comparison = compareResults(r, r, { resamples: 100 });
  assert.ok(comparison.rows.every(row => row.metric !== 'runtime'));
  r.cases[0].lanes.native.runtimeEvidence.stderr = '{}';
  assert.throws(() => validateResult(r), /exhaustion evidence mismatch/);
});

test('compile probes reject stale, partial, missing and failed artifacts', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'bench-probe-'));
  const output = path.join(dir, 'module.wasm');
  const c = { name: 'test', program: 'tests/subsets/s1/flag.bend' };
  const command = body => ({ command: [process.execPath, '-e', body] });
  try {
    const rejected = compileObservation(c, command("process.stderr.write('Unsupported\\tparse\\timport');process.exit(3)"), output);
    assert.equal(rejected.classification, 'Unsupported');
    assert.throws(() => compileObservation(c, command("console.log('Built\\t1')"), output), /Built receipt/);
    writeFileSync(output, 'stale');
    assert.throws(() => compileObservation(c, command(''), output), /fresh/);
    rmSync(output);
    const writes = `require('node:fs').writeFileSync(process.argv[2],'partial');process.stderr.write('Invalid\\tparse\\tsyntax');process.exit(2)`;
    assert.throws(() => compileObservation(c, command(writes), output), /failed compiler emitted/);
    const timedOut = observe([process.execPath, '-e', 'setInterval(()=>{},1000)'], { timeout: 20 });
    assert.equal(outcome(timedOut).classification, 'Exhausted');
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('comparison resolves a named baseline without relaxing compatibility', () => {
  const name = `test-${process.pid}-${Date.now()}`, directory = path.join(LOCAL, 'baselines');
  mkdirSync(directory, { recursive: true });
  const baseline = path.join(directory, `${name}.json`);
  const candidate = path.join(directory, `${name}-candidate.json`);
  try {
    writeFileSync(baseline, JSON.stringify(evidence())); writeFileSync(candidate, JSON.stringify(evidence()));
    const r = observe([process.execPath, path.join(ROOT, 'bench/compare.mjs'), name, candidate, '--resamples=100']);
    assert.equal(r.exit, 0, r.stderr);
    assert.match(r.stdout, /No significant regression/);
  } finally { rmSync(baseline, { force: true }); rmSync(candidate, { force: true }); }
});
