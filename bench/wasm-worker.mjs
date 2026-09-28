#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { fileHash } from './lib/system.mjs';
import { positiveInteger } from './lib/suite.mjs';

export function runtimeFailure(error, profile) {
  if (error instanceof RangeError && /stack/i.test(error.message)) return { classification: 'Exhausted', phase: 'wasm', code: 'call-stack' };
  if (profile === 'knot-fields-wasm-1' && error instanceof WebAssembly.RuntimeError && /unreachable/i.test(error.message)) {
    return { classification: 'Exhausted', phase: 'wasm', code: 'arena-overflow' };
  }
  return { classification: 'HostFailure', phase: 'wasm', code: 'invocation' };
}

function checkedBatch(entry, args, expected, iterations, profile) {
  let result;
  for (let i = 0; i < iterations; i++) {
    try { result = entry(...args); }
    catch (error) { error.outcome = runtimeFailure(error, profile); throw error; }
    if (result !== expected) {
      const error = new Error(`wrong result: expected ${expected}, got ${result} at call ${i}`);
      error.outcome = { classification: 'InternalFailure', phase: 'guard', code: 'wrong-result' };
      throw error;
    }
  }
  return result;
}

export async function measureWasm({ modules, entry, args, expected, warmup, iterations, repeat,
  profile = 'knot-enum-1', minSampleMs = 0 }) {
  if (!['knot-enum-1', 'knot-fields-wasm-1'].includes(profile)) throw new Error('unsupported Wasm profile');
  if (!Number.isFinite(minSampleMs) || minSampleMs < 0 || minSampleMs > 10000) throw new Error('invalid minimum sample duration');
  for (const [name, value] of Object.entries({ warmup, iterations, repeat })) positiveInteger(value, name);
  if (!Number.isInteger(expected) || expected < 0 || expected > 255) throw new Error('expected result must be an enum ordinal');
  if (!Array.isArray(args) || args.some(x => !Number.isInteger(x) || x < 0 || x > 255)) throw new Error('invalid arguments');
  if (!Array.isArray(modules) || !modules.length) throw new Error('no emitted modules');
  const verified = [];
  let fn, lastModule;
  for (const filename of modules) {
    const bytes = readFileSync(filename);
    if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
    const module = await WebAssembly.compile(bytes);
    if (WebAssembly.Module.imports(module).length) throw new Error('Knot profiles require no imports');
    const instance = await WebAssembly.instantiate(module);
    fn = Object.hasOwn(instance.exports, entry) ? instance.exports[entry] : undefined;
    if (typeof fn !== 'function' || fn.length !== args.length) throw new Error('unknown export or wrong live arity');
    const result = checkedBatch(fn, args, expected, 1, profile);
    verified.push({ path: filename, sha256: fileHash(filename), bytes: bytes.length, result, valid: true });
    lastModule = module;
  }
  if (new Set(verified.map(v => v.sha256)).size !== 1) throw new Error('compiler output changed across repetitions');
  const lifecycle = profile === 'knot-fields-wasm-1' ? 'fresh-instance-per-call' : 'persistent-instance';
  // The arena is private and has no reset. Re-instantiation is intentional,
  // timed host work; no emitted bytes or allocator state are patched.
  const invoke = lifecycle === 'fresh-instance-per-call'
    ? (...values) => new WebAssembly.Instance(lastModule).exports[entry](...values) : fn;
  checkedBatch(invoke, args, expected, warmup, profile);
  const samples = [], batches = [];
  for (let i = 0; i < repeat; i++) {
    const start = process.hrtime.bigint();
    let calls = 0, elapsedNs;
    do {
      checkedBatch(invoke, args, expected, iterations, profile);
      calls += iterations;
      elapsedNs = Number(process.hrtime.bigint() - start);
    } while (elapsedNs < minSampleMs * 1e6);
    batches.push({ calls, elapsedNs });
    samples.push(elapsedNs / calls);
  }
  return { samples, batches, lifecycle, profile, verified, valid: true, result: expected,
    checkedCalls: modules.length + warmup + batches.reduce((sum, b) => sum + b.calls, 0) };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(await measureWasm(JSON.parse(readFileSync(process.argv[2], 'utf8')))));
  } catch (error) {
    console.error(JSON.stringify({ message: error.message, outcome: error.outcome ?? { classification: 'HostFailure', phase: 'worker', code: 'setup' } }));
    process.exitCode = 1;
  }
}
