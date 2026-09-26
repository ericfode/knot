#!/usr/bin/env node
// Host adapter only: file I/O, WebAssembly validation/instantiation, invocation.
import fs from 'node:fs/promises';
const [path, name, ...raw] = process.argv.slice(2);
try {
  if (!path || !name || raw.some(x => !/^(0|[1-9][0-9]*)$/.test(x))) throw new Error('expected module export [ordinal ...]');
  const args = raw.map(Number);
  if (args.some(x => !Number.isSafeInteger(x) || x < 0 || x > 255)) throw new Error('ordinal outside enum-profile bounds');
  const bytes = await fs.readFile(path);
  if (!WebAssembly.validate(bytes)) throw new Error('Wasm validation failed');
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length !== 0) throw new Error('enum profile requires no imports');
  const instance = await WebAssembly.instantiate(module);
  const entry = Object.hasOwn(instance.exports, name) ? instance.exports[name] : undefined;
  if (typeof entry !== 'function' || entry.length !== args.length) throw new Error('unknown export or wrong live arity');
  const result = entry(...args);
  if (!Number.isInteger(result) || result < 0 || result > 255) throw new Error('result outside enum-profile bounds');
  console.log(JSON.stringify({validated: true, export: name, arguments: args, result, bytes: bytes.length}));
} catch (error) {
  console.error(`HostFailure\twasm\t${error.message}`);
  process.exitCode = 5;
}
