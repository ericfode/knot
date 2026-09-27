// Usage: node check.mjs BUILD_DIR [name ...]
// Imports each compiled rendering BUILD_DIR/<name>.mjs (compiled by the pinned
// Bend compiler), calls its scenario(n) for n = 0..63, converts the Bend list
// to a JS array, and compares with the independent oracle.
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {scenario as oracle} from './oracle.mjs';

const [, , dir, ...only] = process.argv;
if (!dir) throw new Error('Usage: check.mjs BUILD_DIR [name ...]');
const names = only.length ? only : ['deadpan', 'algebra', 'mythic', 'baroque', 'golf', 'literate'];

function toArray(xs, limit = 10000) {
  const out = [];
  while (xs && xs.$ === 'Con') {
    if (out.length >= limit) throw new Error('list too long');
    out.push(xs.head);
    xs = xs.tail;
  }
  if (!xs || xs.$ !== 'Nil') throw new Error('not a proper Bend list: ' + JSON.stringify(xs));
  return out;
}

const summary = {};
for (const name of names) {
  const path = resolve(dir, `${name}.mjs`);
  if (!existsSync(path)) { summary[name] = {passed: 0, total: 64, firstFailure: 'module missing'}; continue; }
  let mod;
  try {
    mod = (await import(pathToFileURL(path).href)).default;
  } catch (e) {
    summary[name] = {passed: 0, total: 64, firstFailure: 'import failed: ' + e.message}; continue;
  }
  let passed = 0, firstFailure = null;
  for (let n = 0; n < 64; n++) {
    const want = oracle(n);
    let got;
    try {
      got = toArray(mod.scenario(n));
    } catch (e) {
      firstFailure ??= {n, error: String(e && e.message || e)}; continue;
    }
    const same = got.length === want.length && got.every((x, i) => x === want[i]);
    if (same) passed++;
    else firstFailure ??= {n, want, got};
  }
  summary[name] = {passed, total: 64, firstFailure};
}
console.log(JSON.stringify(summary, null, 2));
