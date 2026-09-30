#!/usr/bin/env node
import { randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, statSync, existsSync } from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { metric } from './lib/stats.mjs';
import { loadSuite, positiveInteger } from './lib/suite.mjs';
import { ROOT, LOCAL, SEED_COMMAND, run, observe, fileHash, fingerprint, sourceHashes, harnessHashes } from './lib/system.mjs';
import { outcome, assertSameOutcome } from './lib/outcome.mjs';
import { receiptJSON } from './lib/receipt.mjs';

const LANES = ['native', 'bun'];
const command = (lane, file) => lane === 'native' ? [file] : ['bun', '--no-env-file', file];
const json = object => JSON.stringify(object, null, 2) + '\n';
export const COMPILERS = { 'knot-enum-1': 'src/compile-cli.bend', 'knot-fields-wasm-1': 'tests/compiler-fields-wasm/compile.bend' };

function checkBuild(entry, executable, output) {
  const program = path.join(ROOT, 'tests/subsets/s1/flag.bend');
  if (entry === 'eval-cli') {
    const observed = run([...executable, program, 'flip', 65536, 0]);
    if (observed.stdout !== 'Evaluated\t0\t1\tOn{}') throw new Error('seed-built evaluator failed flag literal guard');
    return { valid: true, result: 1, observation: observed };
  }
  const wasm = `${output}.guard.wasm`, request = `${output}.guard.json`;
  const observed = run([...executable, program, wasm]);
  if (observed.stdout !== `Built\t${statSync(wasm).size}`) throw new Error('seed-built compiler missing Built receipt');
  writeFileSync(request, json({ modules: [wasm], entry: 'flip', args: [0], expected: 1, warmup: 1, iterations: 1, repeat: 1 }));
  const checked = JSON.parse(run([process.execPath, path.join(ROOT, 'bench/wasm-worker.mjs'), request]).stdout);
  return { valid: checked.valid, result: checked.result, observation: observed, module: checked.verified[0] };
}

function build(lane, entry, directory, repeat, source = `src/${entry}.bend`) {
  const samples = [], artifacts = [];
  let output;
  for (let i = 0; i < repeat; i++) {
    output = path.join(directory, `${entry}-${lane}-${i}${lane === 'bun' ? '.js' : ''}`);
    const built = run([...SEED_COMMAND, path.join(ROOT, source), '-o', output]);
    if (statSync(output).size === 0) throw new Error('empty seed output');
    samples.push(built.ms);
    artifacts.push({ ...built, path: output, sha256: fileHash(output),
      correctness: checkBuild(entry, command(lane, output), output) });
  }
  return { metric: metric('ms', samples), artifacts, command: command(lane, output) };
}

function resolveOracle(c, evaluators) {
  if (c.oracle.seed) {
    const record = run([...SEED_COMMAND, path.join(ROOT, c.program)]);
    if (record.stdout !== `${c.oracle.constructor}{}`) throw new Error(`${c.name}: seed disagrees with frozen generator expectation`);
    c.oracle.seedObservation = record;
  }
  if (c.oracle.kind === 'literal') return;
  const observations = LANES.map(lane => {
    const record = run([...evaluators[lane].command, path.join(ROOT, c.program), c.entry, c.oracle.fuel, ...c.args]);
    const match = /^Evaluated\t([0-9]+)\t([0-9]+)\t([A-Za-z_][A-Za-z_0-9]*)\{\}$/.exec(record.stdout);
    if (!match || Number(match[2]) > 255) throw new Error(`${c.name}: evaluator did not return a nullary enum`);
    return { lane, ...record, result: Number(match[2]) };
  });
  if (observations[0].stdout !== observations[1].stdout) throw new Error(`${c.name}: evaluator lanes disagree`);
  if (c.expected !== null && c.expected !== observations[0].result) throw new Error(`${c.name}: evaluator disagrees with generator formula`);
  c.expected = observations[0].result;
  c.oracle.observations = observations;
}

export function compileObservation(c, compiler, output) {
  if (existsSync(output)) throw new Error('compile output must be fresh');
  const observed = observe([...compiler.command, path.join(ROOT, c.program), output, ...(c.compileBudgets ?? [])]);
  const classified = outcome(observed);
  if (classified.classification === 'Success') {
    const bytes = existsSync(output) ? statSync(output).size : 0;
    if (!bytes || observed.stdout !== `Built\t${bytes}`) throw new Error(`${c.name}: missing exact Built receipt`);
    return { ...observed, ...classified, path: output, bytes };
  }
  if (existsSync(output)) throw new Error(`${c.name}: failed compiler emitted an artifact`);
  return { ...observed, ...classified };
}

function checkEvaluation(c, record) {
  if (c.oracle.expectedObservation) {
    if (record.stdout !== c.oracle.expectedObservation) throw new Error(`${c.name}: evaluator disagrees with frozen tree`);
  } else {
    const match = /^Evaluated\t\d+\t(\d+)\t([A-Za-z_][A-Za-z_0-9]*)\{\}$/.exec(record.stdout);
    if (!match || Number(match[1]) !== c.expected || (c.oracle.constructor && match[2] !== c.oracle.constructor)) {
      throw new Error(`${c.name}: evaluator disagrees with frozen enum`);
    }
  }
}

function measureEvaluation(c, evaluator) {
  const argv = [...evaluator.command, path.join(ROOT, c.program), c.entry, c.oracle.fuel ?? 1048576, ...c.args];
  const warmup = observe(argv), classified = outcome(warmup);
  if (classified.classification !== 'Success') {
    if (!['Exhausted', 'Unsupported'].includes(classified.classification)) throw new Error(`${c.name}: evaluator failure: ${json({ ...classified, ...warmup })}`);
    return { status: 'unavailable', ...classified, observations: [warmup] };
  }
  checkEvaluation(c, warmup);
  const observations = Array.from({ length: c.repeat }, () => {
    const r = run(argv); checkEvaluation(c, r); return r;
  });
  return { status: 'measured', classification: 'Success', metric: metric('ms', observations.map(r => r.ms)), warmup, observations };
}

function unavailableRuntime(compilations, runtimeStatus, runtimeEvidence = null) {
  const receipts = compilations.map((r, i) => {
    const module = new WebAssembly.Module(readFileSync(r.path));
    if (WebAssembly.Module.imports(module).length) throw new Error('unexpected Wasm imports');
    return { ...r, sha256: fileHash(r.path), valid: true, result: null, warmup: i === 0 };
  });
  if (new Set(receipts.map(r => r.sha256)).size !== 1) throw new Error('compiler output changed across repetitions');
  return { compile: metric('ms', receipts.slice(1).map(r => r.ms)), size: metric('bytes', receipts.slice(1).map(r => r.bytes)),
    compilations: receipts, runtime: null, runtimeStatus, runtimeEvidence };
}

function measureCase(c, lane, compiler, directory, runtime, probe) {
  const compilations = [];
  // Warm file caches and runtime initialization before recording compile times.
  // Each invocation still starts a fresh compiler process (including Bun startup).
  for (let i = 0; i <= c.repeat; i++) {
    const output = path.join(directory, `${c.name}-${lane}-${i}.wasm`);
    const compiled = i === 0 && probe ? probe : compileObservation(c, compiler, output);
    if (compiled.classification !== 'Success') {
      const error = new Error(`${c.name}: accepted compiler changed classification: ${json(compiled)}`);
      error.outcome = outcome(compiled); throw error;
    }
    compilations.push(compiled);
  }
  if (c.runtimeEligible === false) {
    return unavailableRuntime(compilations, { classification: 'Unsupported', phase: 'host', code: 'structured-result' });
  }
  const request = path.join(directory, `${c.name}-${lane}-runtime.json`);
  writeFileSync(request, json({ modules: compilations.map(r => r.path), entry: c.entry,
    args: c.args, expected: c.expected, profile: c.profile, ...runtime, repeat: c.repeat }));
  // Process startup, file reading, validation and Wasm instantiation are outside
  // the worker's batch timers. Every generated artifact is checked before use.
  const worker = observe([process.execPath, path.join(ROOT, 'bench/wasm-worker.mjs'), request]);
  if (worker.exit !== 0 || worker.error) {
    let failure;
    try { failure = JSON.parse(worker.stderr); } catch { failure = { message: worker.stderr, outcome: outcome(worker) }; }
    if (failure.outcome?.classification === 'Exhausted' && failure.outcome.phase === 'wasm' &&
        ['arena-overflow', 'call-stack'].includes(failure.outcome.code)) return unavailableRuntime(compilations, failure.outcome, worker);
    const error = new Error(`${c.name}: ${failure.message}`); error.outcome = failure.outcome; throw error;
  }
  const measured = JSON.parse(worker.stdout);
  const receipts = compilations.map((r, i) => ({ ...r, ...measured.verified[i], warmup: i === 0 }));
  return {
    compile: metric('ms', receipts.slice(1).map(r => r.ms)),
    runtime: metric('ns/call', measured.samples),
    batches: measured.batches, lifecycle: measured.lifecycle,
    size: metric('bytes', receipts.slice(1).map(r => r.bytes)),
    compilations: receipts,
    correctness: { valid: measured.valid, result: measured.result, checkedCalls: measured.checkedCalls },
  };
}

export function benchmark(options = {}) {
  const suite = loadSuite(options.suite ?? 'hillclimb', options);
  suite.cases = suite.cases.map(c => ({ profile: 'knot-enum-1', runtimeEligible: true, seedValid: true, ...c }));
  const buildRepeat = positiveInteger(options['build-repeat'] ?? 1, 'build-repeat', 1000);
  const id = `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`;
  const name = options.name ?? `${suite.name}-${id}`;
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(name)) throw new Error('baseline name must be a filename slug');
  const defaultOutput = options.baseline ? `baselines/${name}.json` : `results/${suite.name}-${id}.json`;
  const output = options.out ? path.resolve(ROOT, options.out) : path.join(LOCAL, defaultOutput);
  // Refuse overwriting evidence, including an existing named baseline.
  mkdirSync(path.dirname(output), { recursive: true });
  writeFileSync(output, json({ schemaVersion: 2, status: 'incomplete', id }), { flag: 'wx' });
  const directory = path.join(LOCAL, 'runs', id);
  mkdirSync(directory, { recursive: true });
  const result = { schemaVersion: 2, status: 'incomplete', id, name,
    startedAt: new Date().toISOString(), suite: { name: suite.name, path: suite.path, sha256: suite.sha256, caseCount: suite.cases.length },
    protocol: { version: 2, lanes: LANES, compileWarmup: 1, runtime: suite.runtime, buildRepeat,
      compile: 'wall time including process startup and file IO', runtimeMetric: 'checked batches in one Node process per case/lane; fields include fresh instances',
      selfCost: suite.selfCost ? { mode: 'whole-run', compile: ['lex', 'parse', 'check', 'emit'], evaluate: ['lex', 'parse', 'check', 'eval'],
        reason: 'driver.source composes phases without clocks; CLI output has no phase timings. Separate CLI totals include startup, reading and observation/writing; no subtraction.' } : null },
    builds: {}, profileBuilds: {}, evaluatorBuilds: {}, cases: [] };
  let phase = 'fingerprint';
  try {
    result.environment = fingerprint();
    for (const lane of LANES) {
      phase = `build compile-cli (${lane})`;
      console.error(phase);
      result.builds[lane] = build(lane, 'compile-cli', directory, buildRepeat);
      if (suite.cases.some(c => c.profile === 'knot-fields-wasm-1')) {
        phase = `build fields compiler (${lane})`; console.error(phase);
        (result.profileBuilds['knot-fields-wasm-1'] ??= {})[lane] = build(lane, 'compile-fields', directory, buildRepeat, COMPILERS['knot-fields-wasm-1']);
      }
      if (suite.selfCost || suite.cases.some(c => c.oracle.kind === 'evaluator')) {
        phase = `build eval-cli (${lane})`;
        console.error(phase);
        result.evaluatorBuilds[lane] = build(lane, 'eval-cli', directory, 1);
      }
    }
    for (const c of suite.cases) {
      phase = `oracle ${c.name}`;
      resolveOracle(c, result.evaluatorBuilds);
      const record = { ...c, lanes: {} };
      result.cases.push(record);
      const compilers = c.profile === 'knot-enum-1' ? result.builds : result.profileBuilds[c.profile];
      const probes = Object.fromEntries(LANES.map(lane => [lane, compileObservation(c, compilers[lane], path.join(directory, `${c.name}-${lane}-probe.wasm`))]));
      assertSameOutcome(probes.native, probes.bun, c.name);
      record.probes = probes;
      const classification = probes.native.classification;
      if (classification !== 'Success') {
        record.status = 'not-yet-compilable';
        record.classification = classification;
        record.d4Discrepancy = c.seedValid && classification === 'Invalid';
        console.error(`${record.status} ${c.name}: ${classification} ${probes.native.phase}/${probes.native.code}${record.d4Discrepancy ? ' (seed-valid; D4 discrepancy)' : ''}`);
        if (!c.probe || ['HostFailure', 'InternalFailure'].includes(classification)) {
          const error = new Error(`${c.name}: ${json(probes)}`); error.outcome = outcome(probes.native); throw error;
        }
        continue;
      }
      if (!c.seedValid) throw new Error(`${c.name}: compiler accepted a frozen seed-negative program`);
      record.status = 'measured';
      for (const lane of LANES) {
        phase = `${c.name} (${lane})`;
        console.error(`measure ${phase}, ${c.repeat} samples`);
        record.lanes[lane] = measureCase(c, lane, compilers[lane], directory, suite.runtime, probes[lane]);
        if (suite.selfCost) record.lanes[lane].evaluation = measureEvaluation(c, result.evaluatorBuilds[lane]);
      }
      if (suite.selfCost) {
        const a = record.lanes.native.evaluation, b = record.lanes.bun.evaluation;
        if (a.classification !== b.classification || a.observations[0].stdout !== b.observations[0].stdout) throw new Error(`${c.name}: evaluator lanes disagree`);
      }
      if (JSON.stringify(record.lanes.native.runtimeStatus) !== JSON.stringify(record.lanes.bun.runtimeStatus)) throw new Error(`${c.name}: runtime lanes disagree`);
    }
    phase = 'input stability';
    if (JSON.stringify(sourceHashes()) !== JSON.stringify(result.environment.sourceHashes) ||
        JSON.stringify(harnessHashes()) !== JSON.stringify(result.environment.harnessHashes) ||
        fileHash(path.join(ROOT, suite.path)) !== suite.sha256 ||
        suite.cases.some(c => fileHash(path.join(ROOT, c.program)) !== c.sourceSha256) ||
        suite.cases.some(c => c.oracle.manifest && fileHash(path.join(ROOT, c.oracle.manifest)) !== c.oracle.manifestSha256) ||
        suite.cases.some(c => c.oracle.reference && fileHash(path.join(ROOT, c.oracle.reference)) !== c.oracle.referenceSha256) ||
        run(['git', 'rev-parse', 'HEAD']).stdout !== result.environment.git.commit) {
      throw new Error('inputs changed during measurement; discard this run');
    }
    result.status = 'passed';
    result.coverage = { measured: result.cases.filter(c => c.status === 'measured').length,
      notYetCompilable: result.cases.filter(c => c.status === 'not-yet-compilable').length,
      d4Discrepancies: result.cases.filter(c => c.d4Discrepancy).length };
  } catch (error) {
    result.status = 'failed';
    result.failure = { phase, message: error.message, outcome: error.outcome ?? { classification: 'InternalFailure', phase: 'harness', code: 'evidence' } };
  } finally {
    result.finishedAt = new Date().toISOString();
    writeFileSync(output, receiptJSON(result));
    console.log(output);
  }
  if (result.status !== 'passed') throw new Error(`benchmark invalid (${phase}): ${result.failure.message}`);
  return { result, output };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { values } = parseArgs({ options: {
      suite: { type: 'string' }, repeat: { type: 'string' }, out: { type: 'string' },
      warmup: { type: 'string' }, iterations: { type: 'string' }, 'build-repeat': { type: 'string' },
      baseline: { type: 'boolean' }, name: { type: 'string' }, help: { type: 'boolean' },
    } });
    if (values.help) console.log('bench --suite=hillclimb|runtime|recursion|fields-wasm|closures|baseslice|generics|literals|smoke|core|scaling [--repeat=N] [--out=FILE] [--warmup=N] [--iterations=N] [--build-repeat=N]\nbench --baseline [--name=NAME] [same options]; default suite: hillclimb');
    else benchmark(values);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
