#!/usr/bin/env node
import { randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { compareSamples, metric } from './lib/stats.mjs';
import { positiveInteger } from './lib/suite.mjs';
import { ROOT, SEED_COMMAND, childEnv, fileHash, fingerprint, run, sourceHashes, harnessHashes } from './lib/system.mjs';

const MANIFEST = 'tests/compiler-c/cases.json';
const CC = ['cc', '-O2', '-std=c99', '-Wall', '-Werror', '-fwrapv'];
const WASM_HOST = [process.execPath, path.join(ROOT, 'scripts/run-wasm.mjs'), '--profile=knot-fields-wasm-1'];
const json = value => JSON.stringify(value, null, 2) + '\n';
const read = file => JSON.parse(readFileSync(file, 'utf8'));

function execute(argv) {
  const start = process.hrtime.bigint();
  const result = spawnSync(argv[0], argv.slice(1).map(String), {
    cwd: ROOT, env: childEnv, encoding: 'utf8', timeout: 120000, maxBuffer: 4 * 1024 * 1024,
  });
  if (result.error || result.signal) throw new Error(`${argv.join(' ')}: ${result.error?.message || result.signal}`);
  return { argv: argv.map(String), ms: Number(process.hrtime.bigint() - start) / 1e6,
    exit: result.status, stdout: result.stdout.trim(), stderr: result.stderr.trim() };
}

export function checkedProcess(record, expected, kind) {
  if (record.exit !== 0) throw new Error(`${kind}: exit ${record.exit}: ${record.stderr}`);
  if (kind === 'upstream') {
    if (record.stdout.includes('\n') || (record.stdout !== `${expected}{}` && !record.stdout.endsWith(`.${expected}{}`))) {
      throw new Error(`upstream wrong result: ${record.stdout}; expected ${expected}{}`);
    }
  } else {
    const observed = JSON.parse(record.stdout);
    if (observed.result !== expected) throw new Error(`${kind} wrong result: ${record.stdout}; expected ${expected}`);
  }
  return record;
}

function processes(argv, expected, kind, repeat) {
  const observations = [];
  for (let i = 0; i <= repeat; i++) observations.push({ ...checkedProcess(execute(argv), expected, kind), warmup: i === 0 });
  return { metric: metric('ms/process', observations.slice(1).map(x => x.ms)), observations };
}

function built(command, source, output, budgets) {
  const invocation = run([...command, path.join(ROOT, source), output, ...budgets]);
  const bytes = statSync(output).size;
  if (invocation.stdout !== `Built\t${bytes}`) throw new Error(`${source}: missing exact Built receipt`);
  return { ...invocation, output, bytes, sha256: fileHash(output) };
}

function compileProgram(c, compilers, directory, repeat) {
  const records = { c: [], wasm: [] };
  for (let i = 0; i <= repeat; i++) {
    const emitted = built(compilers.c.command, c.file, path.join(directory, `${c.name}-${i}.c`), c.compile_budgets ?? []);
    const executable = path.join(directory, `${c.name}-${i}.native`);
    const cc = run([...CC, emitted.output, '-o', executable]);
    records.c.push({ emitted, cc, executable, warmup: i === 0 });
    records.wasm.push({ ...built(compilers.wasm.command, c.file, path.join(directory, `${c.name}-${i}.wasm`), c.compile_budgets ?? []), warmup: i === 0 });
  }
  if (new Set(records.c.map(x => x.emitted.sha256)).size !== 1 || new Set(records.wasm.map(x => x.sha256)).size !== 1) {
    throw new Error(`${c.name}: nondeterministic compiler output`);
  }
  const cLast = records.c.at(-1), wasmLast = records.wasm.at(-1);
  const worker = path.join(directory, `${c.name}.worker`);
  const workerBuild = run([...CC, '-DKNOT_NO_MAIN', cLast.emitted.output, path.join(ROOT, 'bench/c-native-worker.c'), '-o', worker]);
  return {
    c: { emission: metric('ms', records.c.slice(1).map(x => x.emitted.ms)),
      cc: metric('ms', records.c.slice(1).map(x => x.cc.ms)),
      total: metric('ms', records.c.slice(1).map(x => x.emitted.ms + x.cc.ms)),
      sourceSize: metric('bytes', records.c.slice(1).map(x => x.emitted.bytes)),
      records: records.c, worker, workerBuild },
    wasm: { emission: metric('ms', records.wasm.slice(1).map(x => x.ms)),
      size: metric('bytes', records.wasm.slice(1).map(x => x.bytes)), records: records.wasm },
    comparison: compareSamples(records.wasm.slice(1).map(x => x.ms), records.c.slice(1).map(x => x.emitted.ms + x.cc.ms)),
    outputs: { c: cLast.executable, wasm: wasmLast.output },
  };
}

function upstream(c, call, index, directory, repeat, processRepeat) {
  const wrapper = path.join(directory, `${c.name}-call-${index}.bend`);
  let importPath = path.relative(directory, path.join(ROOT, c.file)).split(path.sep).join('/');
  if (!importPath.startsWith('.')) importPath = `./${importPath}`;
  // The fixture's frozen source expression supplies erased arguments too.
  // This wrapper changes only the entry and adds the seed's required Base.
  writeFileSync(wrapper, `import Base\nimport ${importPath} as F\n\ndef main() -> F.${c.type}:\n  ${call.seed}\n`);
  const records = [];
  let executable;
  for (let i = 0; i <= repeat; i++) {
    executable = path.join(directory, `${c.name}-call-${index}-${i}.upstream`);
    const compiled = execute([...SEED_COMMAND, wrapper, '-o', executable]);
    if (compiled.exit === 1 && /a fresh (?:constructor )?name \(duplicate declaration:/.test(compiled.stderr)) {
      return { status: 'unavailable', reason: 'Base-name collision in the unchanged imported fixture',
        scope: 'entire imported book', wrapper, wrapperSha256: fileHash(wrapper), failure: compiled };
    }
    if (compiled.exit !== 0) throw new Error(`upstream native build: exit ${compiled.exit}: ${compiled.stderr}`);
    records.push({ ...compiled, executable, warmup: i === 0 });
    checkedProcess(execute([executable]), c.constructors[call.tag], 'upstream');
  }
  return { status: 'passed', wrapper, wrapperSha256: fileHash(wrapper),
    compile: metric('ms', records.slice(1).map(x => x.ms)), compilations: records,
    process: processes([executable], c.constructors[call.tag], 'upstream', processRepeat) };
}

function exhausted(argv, prefix) {
  const observation = execute(argv);
  if (observation.exit !== 4 || observation.stdout || !observation.stderr.startsWith(prefix)) {
    throw new Error(`expected ${prefix}, got ${JSON.stringify(observation)}`);
  }
  return { status: 'exhausted', expected: prefix, observation };
}

function measureCall(c, call, index, compilation, directory, settings) {
  const nativeCommand = [compilation.outputs.c, call.export, ...call.arguments];
  const wasmCommand = [...WASM_HOST, compilation.outputs.wasm, call.export, ...call.arguments];
  const record = { ...call, lanes: {} };
  for (const [lane, argv] of [['c', nativeCommand], ['wasm', wasmCommand]]) {
    const prefix = c[`${lane}_exhausted`];
    if (prefix) {
      record.lanes[lane] = exhausted(argv, prefix);
      continue;
    }
    const checkedArtifacts = (lane === 'c' ? compilation.c.records : compilation.wasm.records).map(x => {
      const command = lane === 'c' ? [x.executable, call.export, ...call.arguments]
        : [...WASM_HOST, x.output, call.export, ...call.arguments];
      return checkedProcess(execute(command), call.tag, lane);
    });
    const measured = lane === 'c'
      ? JSON.parse(run([compilation.c.worker, call.export, call.tag, settings.warmup, settings.iterations, settings.repeat, ...call.arguments]).stdout)
      : (() => {
        const request = path.join(directory, `${c.name}-call-${index}.wasm.json`);
        writeFileSync(request, json({ file: compilation.outputs.wasm, entry: call.export,
          args: call.arguments, expected: call.tag, ...settings }));
        return JSON.parse(run([process.execPath, path.join(ROOT, 'bench/c-wasm-worker.mjs'), request]).stdout);
      })();
    if (!measured.valid || measured.result !== call.tag || measured.checkedCalls !== settings.warmup + settings.repeat * settings.iterations ||
        measured.samples?.length !== settings.repeat || measured.samples.some(x => !Number.isFinite(x) || x <= 0)) {
      throw new Error(`${c.name}: invalid ${lane} worker receipt`);
    }
    record.lanes[lane] = { status: 'passed', freshLifetime: metric('ns/call', measured.samples),
      clockResolutionNs: measured.clockResolutionNs ?? null,
      correctness: { checkedCalls: measured.checkedCalls, checkedArtifacts },
      process: processes(argv, call.tag, lane, settings.processRepeat) };
  }
  record.lanes.upstream = compilation.upstreamUnavailable ?? upstream(c, call, index, directory, settings.upstreamRepeat, settings.processRepeat);
  if (record.lanes.upstream.status === 'unavailable') compilation.upstreamUnavailable = record.lanes.upstream;
  if (record.lanes.c.status === 'passed' && record.lanes.wasm.status === 'passed') {
    record.comparisons = {
      cOverWasmFreshLifetime: compareSamples(record.lanes.wasm.freshLifetime.samples, record.lanes.c.freshLifetime.samples),
      cOverWasmProcess: compareSamples(record.lanes.wasm.process.metric.samples, record.lanes.c.process.metric.samples),
    };
    if (record.lanes.upstream.status === 'passed') {
      record.comparisons.cOverUpstreamProcess = compareSamples(record.lanes.upstream.process.metric.samples, record.lanes.c.process.metric.samples);
    }
  }
  return record;
}

export function benchmarkC(options = {}) {
  const settings = Object.fromEntries(Object.entries({ repeat: 7, warmup: 100, iterations: 1000,
    compileRepeat: 3, processRepeat: 3, upstreamRepeat: 3 }).map(([name, fallback]) => [name,
      positiveInteger(options[name] ?? fallback, name, 1000000)]));
  if (settings.repeat > 1000) throw new Error('repeat must be <= 1000');
  const suite = read(path.join(ROOT, MANIFEST));
  const cases = options.only ? suite.cases.filter(c => c.name === options.only) : suite.cases;
  if (!cases.length) throw new Error('no matching benchmark case');
  const id = `${new Date().toISOString().replaceAll(':', '-')}-${randomUUID().slice(0, 8)}`;
  const directory = path.join(ROOT, '.local/bench/c-runs', id);
  const output = options.out ? path.resolve(ROOT, options.out) : path.join(ROOT, '.local/bench/results', `c-${id}.json`);
  mkdirSync(directory, { recursive: true });
  mkdirSync(path.dirname(output), { recursive: true });
  const result = { schemaVersion: 1, status: 'incomplete', id, startedAt: new Date().toISOString(),
    suite: { manifest: MANIFEST, sha256: fileHash(path.join(ROOT, MANIFEST)), profile: suite.profile,
      programs: cases.length, calls: cases.reduce((n, c) => n + c.calls.length, 0),
      staticRejections: suite.rejections.map(c => ({ name: c.name, file: c.file, outcome: c.check })) },
    protocol: { settings, cc: CC, compilerHost: 'native seed-built Bend',
      compile: 'one compiler process reading source and writing artifact; C total adds the separate cc process',
      freshLifetime: 'C reset+dispatch+invoke+check; Wasm instantiate+export lookup+invoke+check; no module compile or process startup',
      process: 'fresh process wall time through checked result; C shim, Node Wasm adapter, or upstream native pure-main printer',
      upstream: 'per-call Base wrapper, seed native CLI default -std=c11 -O3 -lpthread -lm; compiler source recorded by seed digest',
      upstreamUnavailable: 'Base-name collisions retain the seed diagnostic; alias/no-Base controls in bench/c-upstream-probes.json',
      ratio: 'C / reference; timings include different runtime and host overheads and do not isolate generated instruction speed',
      isolation: 'shared host; no CPU affinity, frequency lock or exclusion of concurrent work',
      compilationWarmup: 1, processWarmup: 1, outliersRemoved: false }, builds: {}, cases: [] };
  writeFileSync(output, json(result), { flag: 'wx' });
  let phase = 'fingerprint';
  try {
    result.environment = { ...fingerprint(), cCompiler: { command: 'cc', version: run(['cc', '--version']).stdout } };
    result.environment.nativeWorkerSha256 = fileHash(path.join(ROOT, 'bench/c-native-worker.c'));
    const sourceDigests = Object.fromEntries(cases.map(c => [c.file, fileHash(path.join(ROOT, c.file))]));
    result.suite.sourceHashes = sourceDigests;
    for (const [backend, entry] of [['c', 'tests/compiler-c/compile.bend'], ['wasm', 'tests/compiler-fields-wasm/compile.bend']]) {
      phase = `build ${backend} compiler`;
      console.error(phase);
      const executable = path.join(directory, `${backend}-compiler`);
      result.builds[backend] = { ...run([...SEED_COMMAND, path.join(ROOT, entry), '-o', executable]),
        entry, entrySha256: fileHash(path.join(ROOT, entry)), command: [executable], executableSha256: fileHash(executable) };
    }
    for (const c of cases) {
      phase = `compile ${c.name}`;
      console.error(phase);
      const compilation = compileProgram(c, result.builds, directory, settings.compileRepeat);
      const record = { name: c.name, suite: c.suite, source: c.file, sourceSha256: sourceDigests[c.file],
        originalSource: c.original_file ?? null, evalExhausted: c.eval_exhausted ?? null, compilation, calls: [] };
      result.cases.push(record);
      for (const [index, call] of c.calls.entries()) {
        phase = `measure ${c.name} ${call.export}(${call.arguments.join(',')})`;
        console.error(phase);
        record.calls.push(measureCall(c, call, index, compilation, directory, settings));
      }
      writeFileSync(output, json(result));
    }
    phase = 'input stability';
    if (JSON.stringify(sourceHashes()) !== JSON.stringify(result.environment.sourceHashes) ||
        JSON.stringify(harnessHashes()) !== JSON.stringify(result.environment.harnessHashes) ||
        fileHash(path.join(ROOT, 'bench/c-native-worker.c')) !== result.environment.nativeWorkerSha256 ||
        fileHash(path.join(ROOT, MANIFEST)) !== result.suite.sha256 ||
        Object.values(result.builds).some(b => fileHash(path.join(ROOT, b.entry)) !== b.entrySha256) ||
        Object.entries(sourceDigests).some(([source, digest]) => fileHash(path.join(ROOT, source)) !== digest) ||
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
  return { output, result };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { values } = parseArgs({ options: {
      repeat: { type: 'string' }, warmup: { type: 'string' }, iterations: { type: 'string' },
      'compile-repeat': { type: 'string' }, 'process-repeat': { type: 'string' }, 'upstream-repeat': { type: 'string' },
      only: { type: 'string' }, out: { type: 'string' }, help: { type: 'boolean' },
    } });
    if (values.help) console.log('node bench/c-run.mjs [--only=CASE] [--repeat=7] [--warmup=100] [--iterations=1000] [--compile-repeat=3] [--process-repeat=3] [--upstream-repeat=3] [--out=FILE]');
    else benchmarkC({ ...values, compileRepeat: values['compile-repeat'], processRepeat: values['process-repeat'], upstreamRepeat: values['upstream-repeat'] });
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
