// Persistent-instance boundary probe; no source-language semantics.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const [path, name, rawCount, rawExpected, ...rawArgs] = process.argv.slice(2);
const count = Number(rawCount), expected = Number(rawExpected), args = rawArgs.map(Number);
const bytes = await fs.readFile(path);
assert(WebAssembly.validate(bytes));
const {instance} = await WebAssembly.instantiate(bytes);
const entry = instance.exports[name];
for (let i = 0; i < count; i++) assert.equal(entry(...args), expected);
for (let i = 0; i < 2; i++) {
  assert.throws(() => entry(...args), error => error instanceof WebAssembly.RuntimeError && error.message === 'unreachable');
}
console.log(JSON.stringify({successful: count, overflow: count + 1, repeatedOverflow: true}));
