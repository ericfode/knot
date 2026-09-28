// Persistent-instance allocation probe; no source-language semantics.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const [path, name, rawCount, rawExpected, ...rawArgs] = process.argv.slice(2);
const count = Number(rawCount), expected = Number(rawExpected), args = rawArgs.map(Number);
assert(Number.isSafeInteger(count) && count > 0);
const bytes = await fs.readFile(path);
assert(WebAssembly.validate(bytes));
const {instance} = await WebAssembly.instantiate(bytes);
const entry = instance.exports[name];
assert.equal(typeof entry, 'function');
assert.equal(entry.length, args.length);
let successful = 0;
try {
  while (successful <= count) {
    assert.equal(entry(...args), expected);
    successful++;
  }
  throw new Error('expected bounded arena overflow');
} catch (error) {
  if (!(error instanceof WebAssembly.RuntimeError && error.message === 'unreachable')) throw error;
}
assert.throws(() => entry(...args), error =>
  error instanceof WebAssembly.RuntimeError && error.message === 'unreachable');
console.log(JSON.stringify({successful, overflow: successful + 1, repeatedOverflow: true}));
