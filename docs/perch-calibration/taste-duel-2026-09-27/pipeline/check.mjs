// Usage: node check.mjs BUILD_DIR [name ...]
// Imports BUILD_DIR/<name>.mjs (compiled by the pinned Bend compiler), calls
// its scenario(n) for n = 0..63 and compares with the independent oracle.
// Prints a JSON summary {rendering: {passed, total, firstFailure}} plus the
// oracle's outcome histogram (to show the probes discriminate).
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {scenario as oracle, BASE} from './oracle.mjs';

const [, , dir, ...only] = process.argv;
if (!dir) throw new Error('Usage: check.mjs BUILD_DIR [name ...]');
const names = only.length ? only : ['deadpan', 'algebra', 'mythic', 'baroque', 'golf', 'literate'];

function toArray(xs, limit = 1000) {
  const out = [];
  while (xs?.$ === 'Con') {
    if (out.length >= limit) throw new Error('list too long');
    out.push(xs.head); xs = xs.tail;
  }
  if (xs?.$ !== 'Nil') throw new Error(`not a list: ${JSON.stringify(xs)}`);
  return out;
}

const N = 64;
const histogram = {ok: 0, e1: 0, e2: 0, e3: 0};
for (let n = 0; n < N; n++) for (const code of oracle(n)) {
  if (code % 4 === 0) histogram.ok++; else histogram[`e${code % 4}`]++;
}

const summary = {};
for (const name of names) {
  const path = resolve(dir, `${name}.mjs`);
  if (!existsSync(path)) { summary[name] = {passed: 0, total: N, firstFailure: 'missing module'}; continue; }
  let passed = 0, firstFailure = null;
  try {
    const mod = (await import(pathToFileURL(path).href)).default;
    for (let n = 0; n < N; n++) {
      const want = oracle(n);
      let got;
      try { got = toArray(mod.scenario(n)); } catch (e) { got = `throw: ${e.message}`; }
      if (JSON.stringify(got) === JSON.stringify(want)) passed++;
      else if (!firstFailure) {
        const idx = Array.isArray(got) ? want.findIndex((w, i) => got[i] !== w) : -1;
        firstFailure = {n, input: idx >= 0 ? BASE[idx] : null, want, got};
      }
    }
  } catch (e) {
    firstFailure = `import failed: ${e.message}`;
  }
  summary[name] = {passed, total: N, firstFailure};
}
console.log(JSON.stringify({oracle_histogram: histogram, per_probe_outputs: BASE.length, summary}, null, 1));
