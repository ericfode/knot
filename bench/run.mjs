#!/usr/bin/env node
import { randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { metric } from './lib/stats.mjs';
import { loadSuite, positiveInteger } from './lib/suite.mjs';
import { ROOT, LOCAL, SEED_COMMAND, run, fileHash, fingerprint, sourceHashes, harnessHashes } from './lib/system.mjs';

const LANES = ['native', 'bun'];
const command = (lane, file) => lane === 'native' ? [file] : ['bun', '--no-env-file', file];
const json = object => JSON.stringify(object, null, 2) + '\n';

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

function build(lane, entry, directory, repeat) {
  const samples = [], artifacts = [];
  let output;
  for (let i = 0; i < repeat; i++) {
    output = path.join(directory, `${entry}-${lane}-${i}${lane === 'bun' ? '.js' : ''}`);
    const built = run([...SEED_COMMAND, path.join(ROOT, `src/${entry}.bend`), '-o', output]);
    if (statSync(output).size === 0) throw new Error('empty seed output');
    samples.push(built.ms);
    artifacts.push({ ...built, path: output, sha256: fileHash(output),
      correctness: checkBuild(entry, command(lane, output), output) });
  }
  return { metric: metric('ms', samples), artifacts, command: command(lane, output) };
}

function resolveOracle(c, evaluators) {
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

function measureCase(c, lane, compiler, directory, runtime) {
  const compilations = [];
  // Warm file caches and runtime initialization before recording compile times.
  // Each invocation still starts a fresh compiler process (including Bun startup).
  for (let i = 0; i <= c.repeat; i++) {
    const output = path.join(directory, `${c.name}-${lane}-${i}.wasm`);
    const compiled = run([...compiler.command, path.join(ROOT, c.program), output]);
    const bytes = statSync(output).size;
    if (compiled.stdout !== `Built\t${bytes}`) throw new Error(`${c.name}: missing exact Built receipt`);
    compilations.push({ ...compiled, path: output, bytes });
  }
  const request = path.join(directory, `${c.name}-${lane}-runtime.json`);
  writeFileSync(request, json({ modules: compilations.map(r => r.path), entry: c.entry,
    args: c.args, expected: c.expected, ...runtime, repeat: c.repeat }));
  // Process startup, file reading, validation and Wasm instantiation are outside
  // the worker's batch timers. Every generated artifact is checked before use.
  const measured = JSON.parse(run([process.execPath, path.join(ROOT, 'bench/wasm-worker.mjs'), request]).stdout);
  const receipts = compilations.map((r, i) => ({ ...r, ...measured.verified[i], warmup: i === 0 }));
  return {
    compile: metric('ms', receipts.slice(1).map(r => r.ms)),
    runtime: metric('ns/call', measured.samples),
    size: metric('bytes', receipts.slice(1).map(r => r.bytes)),
    compilations: receipts,
    correctness: { valid: measured.valid, result: measured.result, checkedCalls: measured.checkedCalls },
  };
}

export function benchmark(options = {}) {
  const suite = loadSuite(options.suite ?? 'core', options);
  const buildRepeat = positiveInteger(options['build-repeat'] ?? 1, 'build-repeat', 1000);
  const id = `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`;
  const name = options.name ?? `${suite.name}-${id}`;
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(name)) throw new Error('baseline name must be a filename slug');
  const defaultOutput = options.baseline ? `baselines/${name}.json` : `results/${suite.name}-${id}.json`;
  const output = options.out ? path.resolve(ROOT, options.out) : path.join(LOCAL, defaultOutput);
  // Refuse overwriting evidence, including an existing named baseline.
  mkdirSync(path.dirname(output), { recursive: true });
  writeFileSync(output, json({ schemaVersion: 1, status: 'incomplete', id }), { flag: 'wx' });
  const directory = path.join(LOCAL, 'runs', id);
  mkdirSync(directory, { recursive: true });
  const result = { schemaVersion: 1, status: 'incomplete', id, name,
    startedAt: new Date().toISOString(), suite: { name: suite.name, path: suite.path, sha256: suite.sha256, caseCount: suite.cases.length },
    protocol: { version: 1, lanes: LANES, compileWarmup: 1, runtime: suite.runtime, buildRepeat,
      compile: 'wall time including process startup and file IO', runtimeMetric: 'checked warm calls in one Node process per case/lane' },
    builds: {}, evaluatorBuilds: {}, cases: [] };
  let phase = 'fingerprint';
  try {
    result.environment = fingerprint();
    for (const lane of LANES) {
      phase = `build compile-cli (${lane})`;
      console.error(phase);
      result.builds[lane] = build(lane, 'compile-cli', directory, buildRepeat);
      if (suite.cases.some(c => c.oracle.kind === 'evaluator')) {
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
      for (const lane of LANES) {
        phase = `${c.name} (${lane})`;
        console.error(`measure ${phase}, ${c.repeat} samples`);
        record.lanes[lane] = measureCase(c, lane, result.builds[lane], directory, suite.runtime);
      }
    }
    phase = 'input stability';
    if (JSON.stringify(sourceHashes()) !== JSON.stringify(result.environment.sourceHashes) ||
        JSON.stringify(harnessHashes()) !== JSON.stringify(result.environment.harnessHashes) ||
        fileHash(path.join(ROOT, suite.path)) !== suite.sha256 ||
        suite.cases.some(c => fileHash(path.join(ROOT, c.program)) !== c.sourceSha256) ||
        suite.cases.some(c => c.oracle.manifest && fileHash(path.join(ROOT, c.oracle.manifest)) !== c.oracle.manifestSha256) ||
        run(['git', 'rev-parse', 'HEAD']).stdout !== result.environment.git.commit) {
      throw new Error('inputs changed during measurement; discard this run');
    }
    result.status = 'passed';
  } catch (error) {
    result.status = 'failed';
    result.failure = { phase, message: error.message };
  } finally {
    result.finishedAt = new Date().toISOString();
    writeFileSync(output, json(result));
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
    if (values.help) console.log('bench --suite=smoke|core|scaling [--repeat=N] [--out=FILE] [--warmup=N] [--iterations=N] [--build-repeat=N]\nbench --baseline [--name=NAME] [same options]');
    else benchmark(values);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
