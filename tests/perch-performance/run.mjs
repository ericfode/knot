// Hidden, fixed evaluation vectors and independent arithmetic oracle.
import {writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
const [, , caseId, modulePath, resultPath] = process.argv;
const mod = await import(pathToFileURL(modulePath).href);
const solve = mod.default.call;
if (typeof solve !== 'function') throw new Error('Missing checked public entry');
const list = xs => xs.reduceRight((tail, head) => ({$: 'Con', head, tail}), {$: 'Nil'});
function observe(xs, limit) {
  const out = [];
  while (xs?.$ === 'Con') {
    if (out.length >= limit) throw new Error('Overlong or cyclic result');
    if (!Number.isInteger(xs.head) || xs.head < 0 || xs.head > 0xffffffff) throw new Error('Result is not U32');
    out.push(xs.head); xs = xs.tail;
  }
  if (xs?.$ !== 'Nil') throw new Error('Result is not a standard list');
  return out;
}
function expected(xs) {
  if (caseId === 'growing-prefix-copy') return xs.map(x => (Math.imul(x, 3) + 1) >>> 0);
  if (caseId === 'invariant-summary') {
    const sum = xs.reduce((a, x) => (a + x) >>> 0, 0);
    return xs.map(x => (x + sum) >>> 0);
  }
  if (caseId === 'indexed-linked-list') return xs.map((x, i) => Math.imul(x, i + 1) >>> 0);
  throw new Error('Unknown case');
}
function generated(n, seed) {
  let x = seed >>> 0;
  return Array.from({length: n}, (_, i) => {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0;
    return i % 7 === 0 ? 0xffffffff : i % 5 === 0 ? 7 : x;
  });
}
const probes = [[], [0], [1], [0xffffffff], [1, 2], [2, 1], [4, 4, 4],
  [0xffffffff, 1, 0, 0xffffffff], [7, 0, 7, 3, 7], [0, 0, 0, 0],
  ...[3, 7, 16, 31, 65, 127, 255, 513, 1024].map((n, i) => generated(n, 0x1786d33a + i))];
const correctness = [];
for (let i = 0; i < probes.length; i++) {
  const xs = probes[i], want = expected(xs);
  mod.__gate_start();
  let got, failure;
  try { const result = solve(list(xs)); mod.__gate_stop(); got = observe(result, xs.length + 1); }
  catch (error) { mod.__gate_stop(); failure = String(error); }
  const pass = !failure && JSON.stringify(got) === JSON.stringify(want);
  const mismatch = pass ? -1 : want.findIndex((x, j) => got?.[j] !== x);
  correctness.push({probe: i, n: xs.length, pass, ...(pass ? {} : {failure, mismatch, expected_at_mismatch: want[mismatch], actual_at_mismatch: got?.[mismatch], actual_length: got?.length})});
}
const performance = [];
for (const n of [32, 64, 128, 256, 512, 1024]) {
  const xs = generated(n, 0x628ad317);
  const want = expected(xs);
  const input = list(xs); // Construction is deliberately outside the measurement.
  mod.__gate_start();
  let counts, correct = false, failure;
  try {
    const result = solve(input);
    counts = mod.__gate_stop();
    correct = JSON.stringify(observe(result, n + 1)) === JSON.stringify(want);
  } catch (error) { counts = mod.__gate_stop(); failure = String(error); }
  const work = counts.functions + counts.loops + counts.allocations;
  const previous = performance.at(-1);
  const ratio = previous ? work / previous.work : null;
  const linear_budget = 64 * n + 128;
  performance.push({n, ...counts, work, ratio, linear_budget, correct,
    pass: !failure && correct && work > 0 && work <= linear_budget && (n < 128 || ratio <= 2.65),
    ...(failure ? {failure} : {})});
}
writeFileSync(resultPath, JSON.stringify({
  correctness: {pass: correctness.every(x => x.pass), probes: correctness},
  performance: {pass: performance.every(x => x.pass), metric: 'generated JS function entries + loop iterations + object/array allocations', rows: performance}
}, null, 2) + '\n');
