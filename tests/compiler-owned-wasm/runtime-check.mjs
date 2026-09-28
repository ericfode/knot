import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const [bytesFile, oracleFile] = process.argv.slice(2);
const bytes = Uint8Array.from(JSON.parse(readFileSync(bytesFile, 'utf8')));
assert(WebAssembly.validate(bytes));
const module = new WebAssembly.Module(bytes);
assert.deepEqual(WebAssembly.Module.imports(module), []);
const fresh = () => new WebAssembly.Instance(module).exports;
const words = w => new Uint32Array(w.__heap_memory.buffer);
const snapshot = w => Buffer.from(w.__heap_memory.buffer);
const layouts = [0, 1, 0, 2, 2, 1];
const scalarLayout = [0, 5, 4];
const expected = readFileSync(oracleFile, 'utf8').trim().split('\n').map(JSON.parse);
let allocatorObservations = 0;
let witnesses = 0;

{
  const w = fresh();
  const m = words(w);
  assert.equal(m.byteLength, 131072);
  assert.throws(() => w.__heap_memory.grow(1), RangeError);
  const observe = () => {
    const row = [w.__heap_status(), w.__heap_bump(), w.__heap_live(), m[0], m[1], m[2]];
    for (let address = 65536; address < w.__heap_bump();) {
      const slot = address / 4;
      const count = layouts[m[slot + 2]];
      row.push(address + 12, m[slot], m[slot + 1], count, m[slot + 3]);
      address += 16 + 4 * count;
    }
    assert.deepEqual(row, expected[allocatorObservations], `allocator observation ${allocatorObservations}`);
    allocatorObservations++;
  };
  observe();
  for (const [action, a, b] of [
    ['alloc',0,7],['alloc',2,11],['open',65548],['alloc',0,9],['open',65564],
    ['alloc',2,13],['open',65548],['open',65564],['double',65548],['alloc',1,17],['open',65588],
  ]) {
    if (action === 'alloc') {
      const p = w.__heap_alloc(scalarLayout[a]);
      m[p / 4] = b;
      for (let i = 0; i < a; i++) m[p / 4 + 1 + i] = i + 1;
    } else if (action === 'double') {
      assert.throws(() => w.__heap_open(a), WebAssembly.RuntimeError);
    } else {
      w.__heap_open(a);
    }
    observe();
  }
  assert.equal(allocatorObservations, expected.length);
}
{
  const w = fresh(), p = w.__heap_alloc(0);
  w.__heap_release(p);
  assert.equal(w.__heap_alloc(0), p);
  assert.equal(w.__heap_live(), 1);
  witnesses++;
}
{
  const w = fresh(), m = words(w), p = w.__heap_alloc(2);
  w.__heap_share(p);
  assert.equal(m[p / 4 - 2], 2);
  w.__heap_release(p);
  assert.equal(w.__heap_live(), 1);
  assert.equal(m[p / 4 - 2], 1);
  w.__heap_release(p);
  assert.equal(w.__heap_live(), 0);
  witnesses++;
}
{
  const w = fresh(), m = words(w), child = w.__heap_alloc(2);
  w.__heap_share(child);
  const parent = w.__heap_alloc(3);
  m[parent / 4 + 1] = child;
  m[parent / 4 + 2] = child;
  w.__heap_share(parent);
  w.__heap_open(parent);
  assert.equal(m[child / 4 - 2], 4);
  assert.equal(m[parent / 4 - 2], 1);
  w.__heap_release(parent);
  assert.equal(m[child / 4 - 2], 2);
  w.__heap_release(child);
  w.__heap_release(child);
  assert.equal(w.__heap_live(), 0);
  witnesses++;
}
{
  const w = fresh(), m = words(w), child = w.__heap_alloc(2);
  w.__heap_share(child);
  const parent = w.__heap_alloc(3);
  m[parent / 4 + 1] = child;
  m[parent / 4 + 2] = child;
  w.__heap_share(parent);
  w.__heap_rc_limit(3);
  const before = snapshot(w);
  assert.throws(() => w.__heap_open(parent), WebAssembly.RuntimeError);
  assert.equal(w.__heap_status(), 3);
  assert(before.equals(snapshot(w)), 'shared-open overflow changed memory');
  assert.equal(m[child / 4 - 2], 2);
  assert.equal(m[parent / 4 - 2], 2);
  w.__heap_rc_limit(2147483647);
  w.__heap_release(parent);
  w.__heap_release(parent);
  assert.equal(w.__heap_live(), 0);
  witnesses++;
}
{
  const w = fresh(), m = words(w);
  let p = w.__heap_alloc(0);
  for (let i = 0; i < 64; i++) {
    const next = w.__heap_alloc(1);
    m[next / 4 + 1] = p;
    p = next;
  }
  w.__heap_stack_limit(1);
  assert.equal(w.__heap_enqueue(p), 0);
  const before = snapshot(w);
  assert.equal(w.__heap_clean(0), 3);
  assert(before.equals(snapshot(w)), 'zero budget changed release work');
  assert.equal(w.__heap_live(), 65);
  assert.equal(w.__heap_clean(1), 3);
  assert.equal(w.__heap_clean(10000), 3);
  assert.equal(w.__heap_pending(), 1);
  assert.equal(w.__heap_live(), 65);
  w.__heap_stack_limit(4096);
  assert.equal(w.__heap_clean(10000), 0);
  assert.equal(w.__heap_live(), 0);
  assert.equal(w.__heap_pending(), 0);
  witnesses++;
}
{
  const w = fresh(), m = words(w);
  let p = w.__heap_alloc(0);
  for (let i = 0; i < 3276; i++) {
    const next = w.__heap_alloc(1);
    m[next / 4 + 1] = p;
    p = next;
  }
  assert.equal(w.__heap_live(), 3277);
  const before = snapshot(w);
  assert.throws(() => w.__heap_alloc(0), WebAssembly.RuntimeError);
  assert.equal(w.__heap_status(), 3);
  assert(before.equals(snapshot(w)), 'full allocation changed memory');
  w.__heap_release(p);
  assert.equal(w.__heap_live(), 0);
  assert.equal(w.__heap_peak_pending(), 3277);
  witnesses++;
}
{
  const w = fresh(), p = w.__heap_alloc(0);
  w.__heap_release(p);
  const before = snapshot(w);
  assert.throws(() => w.__heap_release(p), WebAssembly.RuntimeError);
  assert.equal(w.__heap_status(), 5);
  assert.equal(w.__heap_live(), 0);
  assert(before.equals(snapshot(w)), 'double release changed memory');
  witnesses++;
}
{
  const w = fresh(), p = w.__heap_alloc(0);
  const before = snapshot(w);
  assert.throws(() => w.__heap_share(p), WebAssembly.RuntimeError);
  assert.equal(w.__heap_status(), 5);
  assert(before.equals(snapshot(w)), 'Type share changed memory');
  w.__heap_release(p);
  witnesses++;
}
{
  const w = fresh(), p = w.__heap_alloc(0);
  w.__heap_stack_limit(0);
  const before = snapshot(w);
  assert.equal(w.__heap_enqueue(p), 3);
  assert.equal(w.__heap_pending(), 0);
  assert.equal(w.__heap_live(), 1);
  assert(before.equals(snapshot(w)), 'full enqueue lost owner');
  w.__heap_stack_limit(4096);
  w.__heap_release(p);
  witnesses++;
}
{
  const w = fresh(), p = w.__heap_alloc(2);
  w.__heap_rc_limit(1);
  const before = snapshot(w);
  assert.throws(() => w.__heap_share(p), WebAssembly.RuntimeError);
  assert.equal(w.__heap_status(), 3);
  assert(before.equals(snapshot(w)), 'share overflow changed memory');
  w.__heap_rc_limit(2);
  w.__heap_share(p);
  w.__heap_release(p);
  w.__heap_release(p);
  assert.equal(w.__heap_live(), 0);
  witnesses++;
}
console.log(JSON.stringify({status:'pass', allocator_observations:allocatorObservations, runtime_witnesses:witnesses,
  memory_bytes:131072, maximum_chain_cells:3277, law_boundary:'model semantics and emitted kernels; no universal refinement theorem'}));
