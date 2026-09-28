import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { measureFreshWasm } from './c-wasm-worker.mjs';
import { checkedProcess } from './c-run.mjs';
import { ROOT, run } from './lib/system.mjs';

const base = path.join(ROOT, '.local/bench');
mkdirSync(base, { recursive: true });
const directory = mkdtempSync(path.join(base, 'c-tests-'));
const wasm = path.join(directory, 'counter.wasm');
// A mutable counter returns 1 only on a fresh instance. No compiler is involved.
writeFileSync(wasm, Buffer.from('0061736d010000000105016000017f030201000606017f0141000b07090105636f756e7400000a0d010b00230041016a240023000b', 'hex'));
const request = { file: wasm, entry: 'count', args: [], expected: 1, warmup: 3, iterations: 5, repeat: 7 };

test('Wasm worker resets instance lifetime and checks every timed call', () => {
  const result = measureFreshWasm(request);
  assert.equal(result.checkedCalls, 38);
  assert.equal(result.result, 1);
  assert.equal(result.samples.length, 7);
  assert.ok(result.samples.every(x => Number.isFinite(x) && x > 0));
});

test('Wasm worker refuses a wrong result', () => {
  assert.throws(() => measureFreshWasm({ ...request, expected: 0 }), /wrong result/);
});

test('Wasm worker refuses an unknown export and wrong arity', () => {
  assert.throws(() => measureFreshWasm({ ...request, entry: 'missing' }), /unknown export/);
  assert.throws(() => measureFreshWasm({ ...request, args: [0] }), /wrong live arity/);
});

test('process guard distinguishes results from a successful exit alone', () => {
  const observed = { exit: 0, stdout: '{"result":1}', stderr: '' };
  assert.equal(checkedProcess(observed, 1, 'c'), observed);
  assert.throws(() => checkedProcess(observed, 0, 'c'), /wrong result/);
  assert.throws(() => checkedProcess({ ...observed, exit: 4 }, 1, 'c'), /exit 4/);
  assert.throws(() => checkedProcess({ ...observed, stdout: 'X.Off{}' }, 'On', 'upstream'), /wrong result/);
});

const stub = path.join(directory, 'counter.c'), native = path.join(directory, 'counter');
writeFileSync(stub, '#include <stdint.h>\n#include <stddef.h>\nstatic uint32_t count;\nvoid knot_reset(void) { count = 0; }\nuint32_t knot_invoke(const char *name, size_t argc, const uint32_t *args) { (void)name; (void)argc; (void)args; return ++count; }\n');
run(['cc', '-O2', '-std=c99', '-Wall', '-Werror', '-fwrapv', stub, path.join(ROOT, 'bench/c-native-worker.c'), '-o', native]);

test('native worker resets each invocation and retains all timing samples', () => {
  const result = JSON.parse(run([native, 'count', 1, 3, 1000, 7]).stdout);
  assert.equal(result.checkedCalls, 7003);
  assert.equal(result.result, 1);
  assert.equal(result.samples.length, 7);
  assert.ok(result.samples.every(x => Number.isFinite(x) && x > 0));
});

test('native worker rejects wrong results and zero iterations', () => {
  const wrong = spawnSync(native, ['count', '0', '3', '5', '7'], { encoding: 'utf8' });
  assert.equal(wrong.status, 1);
  assert.match(wrong.stderr, /wrong result/);
  const zero = spawnSync(native, ['count', '1', '3', '0', '7'], { encoding: 'utf8' });
  assert.equal(zero.status, 1);
  assert.match(zero.stderr, /invalid benchmark counts/);
});
