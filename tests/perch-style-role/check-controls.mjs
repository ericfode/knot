// Run against libraries emitted by the pinned Bend compiler. No candidate code
// is used by either oracle. The Life fixtures are copied unchanged from the
// original life-blueberry experiment at 2cab333.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {fixtures, compositions, evolve} from './life-oracle.mjs';

const [, , moduleDir, output] = process.argv;
if (!moduleDir || !output) throw new Error('Usage: check-controls.mjs MODULE_DIR OUTPUT.json');
const sha = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const list = xs => xs.reduceRight((tail, head) => ({$: 'Con', head, tail}), {$: 'Nil'});
function observe(xs, limit) {
  const out = [];
  while (xs?.$ === 'Con') {
    assert.ok(out.length < limit, 'unexpected output length');
    out.push(xs.head); xs = xs.tail;
  }
  assert.equal(xs?.$, 'Nil');
  return out;
}
const results = [];
for (const id of ['D01', 'D02', 'H01', 'H02']) {
  const path = resolve(moduleDir, `${id}.mjs`);
  const mod = (await import(pathToFileURL(path).href)).default;
  let cases = 0, laws = 0;
  if (id.startsWith('D')) {
    for (const f of fixtures) {
      const input = list(f.cells);
      const got = f.turns === 1 ? mod.step(f.width, f.height, input)
        : mod.evolve(BigInt(f.turns), f.width, f.height, input);
      assert.deepEqual(observe(got, f.cells.length), f.expected, `${id}:${f.id}`);
      assert.deepEqual(observe(input, f.cells.length), f.cells, 'input preserved');
      cases++;
    }
    for (const f of compositions) {
      const first = mod.evolve(BigInt(f.a), f.width, f.height, list(f.cells));
      const composed = mod.evolve(BigInt(f.b), f.width, f.height, first);
      const direct = mod.evolve(BigInt(f.a + f.b), f.width, f.height, list(f.cells));
      assert.deepEqual(observe(composed, f.cells.length), evolve(f.width, f.height, f.cells, f.a + f.b));
      assert.deepEqual(observe(direct, f.cells.length), evolve(f.width, f.height, f.cells, f.a + f.b));
      laws++;
    }
  } else {
    const indices = Array.from({length: 32}, (_, i) => i);
    const masks = [...new Set([
      ...Array.from({length: 256}, (_, i) => i),
      ...indices.flatMap(i => [2 ** i, 0xffffffff - 2 ** i]),
      0xffffffff, 0xaaaaaaaa, 0x55555555,
    ])];
    const inputs = [[], indices, [...indices].reverse(), [0, 0, 31, 31, 7, 7], [31], [0]];
    for (const mask of masks) for (const xs of inputs) {
      const input = list(xs);
      // Arithmetic oracle is independent of the candidate's bitwise operations.
      const expected = xs.filter(i => Math.floor(mask / 2 ** i) % 2 === 1);
      assert.deepEqual(observe(mod.select(mask, input), xs.length), expected, `${id}:${mask}:${xs}`);
      assert.deepEqual(observe(input, xs.length), xs, 'input preserved');
      cases++;
    }
  }
  results.push({id, passed: true, cases, composition_laws: laws, compiled_sha256: sha(path),
    source_sha256: sha(new URL(`${id}.bend`, import.meta.url))});
}
const report = {passed: true, runtime: process.version, bun: process.versions.bun ?? null,
  life_oracle_sha256: sha(new URL('life-oracle.mjs', import.meta.url)), results};
writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
