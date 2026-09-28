#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { positiveInteger } from './lib/suite.mjs';

// A fresh instance is the current fields profile's only arena reset operation.
// Include it in the timer; compile/validation and process startup remain outside.
export function measureFreshWasm({ file, entry, args, expected, warmup, iterations, repeat }) {
  for (const [name, value] of Object.entries({ warmup, iterations, repeat })) positiveInteger(value, name);
  if (!Number.isInteger(expected) || expected < 0 || expected > 255 ||
      !Array.isArray(args) || args.some(x => !Number.isInteger(x) || x < 0 || x > 255)) {
    throw new Error('expected and arguments must be enum ordinals');
  }
  const bytes = readFileSync(file);
  if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
  const module = new WebAssembly.Module(bytes);
  if (WebAssembly.Module.imports(module).length) throw new Error('unexpected Wasm imports');
  let checkedCalls = 0;
  const batch = count => {
    for (let i = 0; i < count; i++) {
      const instance = new WebAssembly.Instance(module);
      const fn = Object.hasOwn(instance.exports, entry) ? instance.exports[entry] : undefined;
      if (typeof fn !== 'function' || fn.length !== args.length) throw new Error('unknown export or wrong live arity');
      const result = fn(...args);
      if (result !== expected) throw new Error(`wrong result: expected ${expected}, got ${result} at call ${i}`);
      checkedCalls++;
    }
  };
  batch(warmup);
  const samples = [];
  for (let i = 0; i < repeat; i++) {
    const start = process.hrtime.bigint();
    batch(iterations);
    samples.push(Number(process.hrtime.bigint() - start) / iterations);
  }
  return { samples, valid: true, result: expected, checkedCalls };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    console.log(JSON.stringify(measureFreshWasm(JSON.parse(readFileSync(process.argv[2], 'utf8')))));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
