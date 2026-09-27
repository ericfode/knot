// Usage: node check-ablations.mjs BUILD_DIR [name ...]
// Same probe and decoding logic as ../check.mjs, with selectable module names.
// Imports each BUILD_DIR/<name>.mjs, runs scenario(n) for n = 0..63, compares
// with the unchanged independent oracle and prints a JSON summary.
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {scenario as oracle} from '../oracle.mjs';

const dir = process.argv[2];
if (!dir) throw new Error('Usage: check-ablations.mjs BUILD_DIR [name ...]');
const names = process.argv.length > 3 ? process.argv.slice(3) : ['algebra-nolaws', 'algebra-words'];
const toArray = (xs, limit = 64) => {
  const out = [];
  while (xs && xs.$ === 'Con') {
    if (out.length >= limit) throw new Error('list too long');
    out.push(xs.head); xs = xs.tail;
  }
  if (!xs || xs.$ !== 'Nil') throw new Error('not a proper list');
  return out;
};
const summary = {};
for (const name of names) {
  const path = resolve(dir, `${name}.mjs`);
  if (!existsSync(path)) { summary[name] = {passed: 0, total: 64, firstFailure: 'missing module'}; continue; }
  let passed = 0, firstFailure = null;
  try {
    const mod = (await import(pathToFileURL(path).href)).default;
    for (let n = 0; n < 64; n++) {
      const want = oracle(n);
      let got;
      try { got = toArray(mod.scenario(n)); } catch (e) { got = `error: ${e.message}`; }
      if (JSON.stringify(got) === JSON.stringify(want)) passed++;
      else if (!firstFailure) firstFailure = {n, want, got};
    }
  } catch (e) { firstFailure = `import error: ${e.message}`; }
  summary[name] = {passed, total: 64, firstFailure};
}
console.log(JSON.stringify(summary, null, 1));
