import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { measureWasm } from '../wasm-worker.mjs';
import { generatedPrograms } from '../generate.mjs';

test('worker checks every module, warmup and measured call without a compiler', async () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'knot-bench-wasm-'));
  // Independent hand-encoded Wasm: flip(i32) -> i32.const 1.
  const bytes = Buffer.from('0061736d0100000001060160017f017f0302010007080104666c697000000a0601040041010b', 'hex');
  const module = path.join(dir, 'constant.wasm');
  writeFileSync(module, bytes);
  const config = { modules: [module, module], entry: 'flip', args: [0], expected: 1, warmup: 7, iterations: 100, repeat: 3 };
  try {
    const measured = await measureWasm(config);
    assert.equal(measured.checkedCalls, 309);
    assert.equal(measured.samples.length, 3);
    assert.ok(measured.samples.every(n => n > 0));
    assert.ok(measured.verified.every(v => v.valid && v.result === 1));
    await assert.rejects(measureWasm({ ...config, expected: 0 }), /wrong result/);
    await assert.rejects(measureWasm({ ...config, entry: 'missing' }), /unknown export/);
    await assert.rejects(measureWasm({ ...config, args: [] }), /arity/);
    await assert.rejects(measureWasm({ ...config, expected: 256 }), /enum ordinal/);
    const invalid = path.join(dir, 'invalid.wasm');
    writeFileSync(invalid, 'not Wasm');
    await assert.rejects(measureWasm({ ...config, modules: [module, invalid] }), /validation failed/);
    const changed = path.join(dir, 'changed.wasm');
    writeFileSync(changed, Buffer.concat([bytes, Buffer.from([0, 2, 1, 120])]));
    await assert.rejects(measureWasm({ ...config, modules: [module, changed] }), /changed across repetitions/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test('generated workload sources and formula cross-checks are deterministic', () => {
  const first = generatedPrograms();
  assert.deepEqual(first, generatedPrograms());
  assert.equal(first.length, 9);
  assert.equal(new Set(first.map(p => p.program)).size, 9);
  assert.ok(first.every(p => p.source.length < 65536 && p.expected >= 0 && p.expected <= 255));
});
