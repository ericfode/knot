#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { fileHash } from './lib/system.mjs';
import { positiveInteger } from './lib/suite.mjs';

function checkedBatch(entry, args, expected, iterations) {
  let result;
  for (let i = 0; i < iterations; i++) {
    result = entry(...args);
    if (result !== expected) throw new Error(`wrong result: expected ${expected}, got ${result} at call ${i}`);
  }
  return result;
}

export async function measureWasm({ modules, entry, args, expected, warmup, iterations, repeat }) {
  for (const [name, value] of Object.entries({ warmup, iterations, repeat })) positiveInteger(value, name);
  if (!Number.isInteger(expected) || expected < 0 || expected > 255) throw new Error('expected result must be an enum ordinal');
  if (!Array.isArray(args) || args.some(x => !Number.isInteger(x) || x < 0 || x > 255)) throw new Error('invalid arguments');
  if (!Array.isArray(modules) || !modules.length) throw new Error('no emitted modules');
  const verified = [];
  let fn;
  for (const filename of modules) {
    const bytes = readFileSync(filename);
    if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
    const module = await WebAssembly.compile(bytes);
    if (WebAssembly.Module.imports(module).length) throw new Error('enum profile requires no imports');
    const instance = await WebAssembly.instantiate(module);
    fn = Object.hasOwn(instance.exports, entry) ? instance.exports[entry] : undefined;
    if (typeof fn !== 'function' || fn.length !== args.length) throw new Error('unknown export or wrong live arity');
    const result = checkedBatch(fn, args, expected, 1);
    verified.push({ path: filename, sha256: fileHash(filename), bytes: bytes.length, result, valid: true });
  }
  if (new Set(verified.map(v => v.sha256)).size !== 1) throw new Error('compiler output changed across repetitions');
  checkedBatch(fn, args, expected, warmup);
  const samples = [];
  for (let i = 0; i < repeat; i++) {
    const start = process.hrtime.bigint();
    checkedBatch(fn, args, expected, iterations);
    samples.push(Number(process.hrtime.bigint() - start) / iterations);
  }
  return { samples, verified, valid: true, result: expected,
    checkedCalls: modules.length + warmup + repeat * iterations };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(await measureWasm(JSON.parse(readFileSync(process.argv[2], 'utf8')))));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
