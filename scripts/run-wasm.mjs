#!/usr/bin/env node
// Host adapter only: file I/O, WebAssembly validation/instantiation, invocation.
import fs from 'node:fs/promises';
const argv = process.argv.slice(2);
const profile = argv[0]?.startsWith('--profile=') ? argv.shift().slice(10) : 'knot-enum-1';
const [path, name, ...raw] = argv;
let invoking = false;
// Fail closed: only a completed, reported result clears the host-failure code.
process.exitCode = 5;
try {
  if (!['knot-enum-1', 'knot-fields-wasm-1', 'knot-literals-wasm-1'].includes(profile)) throw new Error('unknown Wasm profile');
  if (!path || !name || raw.some(x => !/^(0|[1-9][0-9]*)$/.test(x))) throw new Error('expected module export [ordinal ...]');
  const args = raw.map(Number);
  if (args.some(x => !Number.isSafeInteger(x) || x < 0 || x > 255)) throw new Error('ordinal outside enum-profile bounds');
  const bytes = await fs.readFile(path);
  if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Knot profiles require no imports');
  const instance = await WebAssembly.instantiate(module);
  const entry = Object.hasOwn(instance.exports, name) ? instance.exports[name] : undefined;
  if (typeof entry !== 'function' || entry.length !== args.length) throw new Error('unknown export or wrong live arity');
  invoking = true;
  const result = entry(...args);
  invoking = false;
  if (!Number.isInteger(result) || result < 0 || result > 255) throw new Error('result outside enum-profile bounds');
  console.log(JSON.stringify({validated: true, export: name, arguments: args, result, bytes: bytes.length}));
  process.exitCode = 0;
} catch (error) {
  // The fields profile's only unreachable is the bounded arena guard. Profile
  // selection asserts compiler provenance; this is not an arbitrary-Wasm ABI.
  const stack = invoking && error instanceof RangeError && /maximum call stack size exceeded/i.test(error.message);
  const arena = invoking && profile === 'knot-fields-wasm-1' && error instanceof WebAssembly.RuntimeError && error.message === 'unreachable';
  const bounded = invoking && profile === 'knot-literals-wasm-1' && error instanceof WebAssembly.RuntimeError && error.message === 'unreachable';
  if (stack || arena || bounded) {
    console.error(`Exhausted\twasm\t${stack ? 'call-stack' : bounded ? 'resource-limit' : 'arena-overflow'}`);
    process.exitCode = 4;
  } else {
    console.error(`HostFailure\twasm\t${error.message}`);
    process.exitCode = 5;
  }
}
