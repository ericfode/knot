#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import os from 'node:os';
import { metric, compareSamples } from './lib/stats.mjs';
import { snapshot } from '../tests/compiler-owned-wasm/host.mjs';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const here = path.join(root, 'tests/compiler-owned-wasm');
const build = path.join(root, '.local/compiler-owned-wasm/gate');
const seed = ['bun', '--no-env-file', path.join(root, '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts')];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const readJson = async file => JSON.parse(await fs.readFile(file, 'utf8'));
function require(condition, detail) { if (!condition) throw new Error(detail); }
function run(argv) {
  const result = spawnSync(argv[0], argv.slice(1).map(String), {
    cwd: root, env: { ...process.env, BEND_NO_TELEMETRY: '1' }, encoding: 'utf8', timeout: 120000,
  });
  require(result.status === 0, JSON.stringify({ argv, status: result.status, stdout: result.stdout, stderr: result.stderr, error: result.error?.message }));
  return { argv, stdout: result.stdout, stderr: result.stderr };
}

async function moduleAt(file, expectedHash) {
  const bytes = await fs.readFile(file);
  require(hash(bytes) === expectedHash, `artifact drift: ${file}`);
  require(WebAssembly.validate(bytes), `invalid artifact: ${file}`);
  const module = await WebAssembly.compile(bytes);
  require(WebAssembly.Module.imports(module).length === 0, 'unexpected Wasm imports');
  return { module, file, sha256: hash(bytes), bytes: bytes.length };
}

async function sample(artifact, profile, workload) {
  const exports = (await WebAssembly.instantiate(artifact.module)).exports;
  const entry = exports[workload.export];
  require(typeof entry === 'function' && entry.length === workload.arguments.length, 'missing benchmark entry');
  for (let i = 0; i < workload.warmup; i++) require(entry(...workload.arguments) === workload.tag, 'warmup result differs');
  const before = profile === 'owned' ? snapshot(exports) : null;
  const start = performance.now();
  for (let i = 0; i < workload.iterations; i++) require(entry(...workload.arguments) === workload.tag, 'timed result differs');
  const elapsed = performance.now() - start;
  const after = profile === 'owned' ? snapshot(exports) : null;
  if (after) require(after.live === 0 && after.pending === 0 && after.status === 0, 'timed call leaked ownership');
  return { ns_per_call: elapsed * 1e6 / workload.iterations, before, after,
    measured_allocations: after ? after.allocations - before.allocations : null };
}

async function main() {
  const suite = await readJson(path.join(root, 'bench/owned.json'));
  let repeat = suite.repeat;
  let output = path.join(root, '.local/bench/results', `owned-${Date.now()}.json`);
  for (const arg of process.argv.slice(2)) {
    if (arg.startsWith('--repeat=')) repeat = Number(arg.slice(9));
    else if (arg.startsWith('--out=')) output = path.resolve(root, arg.slice(6));
    else throw new Error(`unknown option ${arg}`);
  }
  require(Number.isSafeInteger(repeat) && repeat >= 3 && repeat <= 100, 'repeat must be 3..100');
  const gatePath = path.join(here, 'receipts/owned-wasm.json');
  const gateBytes = await fs.readFile(gatePath);
  const gate = JSON.parse(gateBytes);
  require(gate.status === 'passed', 'run the complete owned Wasm gate first');
  for (const [file, expected] of Object.entries(gate.inputs)) {
    require(hash(await fs.readFile(path.join(root, file))) === expected, `source changed after gate: ${file}`);
  }
  const result = { schema: 1, status: 'incomplete', date: new Date().toISOString(), suite, repeat,
    gate_sha256: hash(gateBytes), environment: {
      node: process.version, bun: run(['bun', '--version']).stdout.trim(),
      platform: process.platform, architecture: process.arch, release: os.release(),
      cpu: os.cpus()[0]?.model, logical_cpus: os.cpus().length, memory_bytes: os.totalmem(),
    }, inputs: {}, workloads: [] };
  for (const file of ['bench/owned.json', 'bench/owned.mjs', 'bench/lib/stats.mjs', 'tests/compiler-owned-wasm/host.mjs']) {
    result.inputs[file] = hash(await fs.readFile(path.join(root, file)));
  }
  const wrapperDir = path.join(root, '.local/bench/owned');
  await fs.mkdir(wrapperDir, { recursive: true });
  for (const workload of suite.cases) {
    const source = path.join(root, workload.source);
    const wrapper = path.join(wrapperDir, `${workload.name}-reference.bend`);
    const imported = path.relative(wrapperDir, source);
    await fs.writeFile(wrapper, `import ${imported} as F\n\ndef main() -> F.${workload.type}:\n  F.${workload.export}()\n`);
    const reference = run([...seed, wrapper]);
    require(reference.stdout.trim() === imported.replace(/\.bend$/, '') + '.' + workload.tree, 'benchmark seed expectation differs');
    const entry = { name: workload.name, source: workload.source, source_sha256: hash(await fs.readFile(source)), reference, lanes: {} };
    const fixture = gate.fixtures.find(item => item.name === workload.fixture);
    require(fixture, 'benchmark fixture absent from accepted gate');
    for (const lane of ['native', 'bun']) {
      const runtime = lane === 'bun' ? ['bun', '--no-env-file'] : [];
      const executable = path.join(build, lane === 'bun' ? 'eval.js' : 'eval');
      const expectedBuild = gate.builds.find(item => item.lane === lane && item.phase === 'eval');
      require(hash(await fs.readFile(executable)) === expectedBuild.sha256, 'evaluator build drift');
      const evaluator = run([...runtime, executable, source, workload.export, 1048576]);
      require(evaluator.stdout.trim() === `Evaluated\t${workload.type_id}\t${workload.tag}\t${workload.tree}`, 'benchmark evaluator expectation differs');
      const owned = await moduleAt(path.join(build, `${workload.fixture}-${lane}.wasm`), fixture.lanes[lane].sha256);
      const arenaEntry = workload.fixture === 'recursive-reuse'
        ? gate.boundaries.find(item => item.name === 'arena-exhaustion-control' && item.lane === lane)
        : gate.legacy.find(item => item.case === workload.fixture && item.lane === lane && item.profile === 'fields');
      const arenaFile = workload.fixture === 'recursive-reuse'
        ? path.join(build, `reuse-arena-${lane}.wasm`)
        : path.join(build, `legacy-fields-${workload.fixture}-${lane}.wasm`);
      const fields = await moduleAt(arenaFile, arenaEntry.sha256);
      const samples = { fields: [], owned: [] };
      for (let i = 0; i < repeat; i++) {
        for (const profile of i % 2 ? ['owned', 'fields'] : ['fields', 'owned']) {
          samples[profile].push(await sample(profile === 'owned' ? owned : fields, profile, workload));
        }
      }
      const metrics = Object.fromEntries(Object.entries(samples).map(([profile, rows]) =>
        [profile, { runtime: metric('ns/call', rows.map(row => row.ns_per_call)), observations: rows,
          module: { sha256: (profile === 'owned' ? owned : fields).sha256, bytes: (profile === 'owned' ? owned : fields).bytes },
          reserved_memory_bytes: profile === 'owned' ? samples.owned[0].after.memory_bytes : 65536 }]));
      entry.lanes[lane] = { evaluator, ...metrics,
        comparison: compareSamples(samples.fields.map(row => row.ns_per_call), samples.owned.map(row => row.ns_per_call)) };
      process.stderr.write(`owned bench ${workload.name}/${lane}: arena ${metrics.fields.runtime.median.toFixed(1)} ns, owned ${metrics.owned.runtime.median.toFixed(1)} ns\n`);
    }
    result.workloads.push(entry);
  }
  for (const [file, expected] of Object.entries(result.inputs)) require(hash(await fs.readFile(path.join(root, file))) === expected, 'benchmark harness changed while timing');
  for (const [file, expected] of Object.entries(gate.inputs)) require(hash(await fs.readFile(path.join(root, file))) === expected, 'compiler changed while timing');
  result.status = 'passed';
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  process.stdout.write(output + '\n');
}

main().catch(error => { process.stderr.write(`owned benchmark failed: ${error.message}\n`); process.exitCode = 1; });
