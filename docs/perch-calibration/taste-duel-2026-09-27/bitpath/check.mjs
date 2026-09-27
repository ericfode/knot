// Usage: node check.mjs BUILD_DIR [name ...]
// Imports each compiled rendering BUILD_DIR/<name>.mjs, runs scenario(n) for
// n = 0..63, and compares with the independent oracle. Compiles nothing.
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {scenario as oracle} from './oracle.mjs';

const [, , dir, ...names] = process.argv;
if (!dir) throw new Error('Usage: node check.mjs BUILD_DIR [name ...]');
const renderings = names.length ? names
  : ['deadpan', 'algebra', 'mythic', 'baroque', 'golf', 'literate'];

function toArray(xs) {
  const out = [];
  while (xs && xs.$ === 'Con') {
    if (out.length > 1000) throw new Error('list too long');
    out.push(xs.head);
    xs = xs.tail;
  }
  if (!xs || xs.$ !== 'Nil') throw new Error('not a Bend list');
  return out;
}

const summary = {};
for (const name of renderings) {
  const path = resolve(dir, `${name}.mjs`);
  const total = 64;
  if (!existsSync(path)) { summary[name] = {passed: 0, total, firstFailure: 'module missing'}; continue; }
  const mod = (await import(pathToFileURL(path).href)).default;
  let passed = 0, firstFailure = null;
  for (let n = 0; n < total; n++) {
    const want = oracle(n);
    let got;
    try { got = toArray(mod.scenario(n)); } catch (e) { got = `threw: ${e}`; }
    if (JSON.stringify(got) === JSON.stringify(want)) passed++;
    else if (!firstFailure) firstFailure = {n, want, got};
  }
  summary[name] = {passed, total, firstFailure};
}
console.log(JSON.stringify(summary, null, 1));
