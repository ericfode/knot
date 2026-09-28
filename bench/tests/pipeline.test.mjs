import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { compilerSelection } from '../run.mjs';
import { expectedResult } from '../lib/suite.mjs';
import { ROOT, LOCAL, entryHashes, hash } from '../lib/system.mjs';

test('pipeline selection preserves the default compiler and isolates the optional entries', () => {
  assert.deepEqual(compilerSelection(), { pipeline: 'default', entry: 'src/compile-cli.bend', profile: 'knot-enum-1' });
  assert.deepEqual(compilerSelection('off'), { pipeline: 'off', entry: 'tests/compiler-fields-wasm/compile.bend', profile: 'knot-fields-wasm-1' });
  assert.deepEqual(compilerSelection('on'), { pipeline: 'on', entry: 'tests/compiler-opt/compile.bend', profile: 'knot-fields-wasm-1' });
  for (const invalid of ['auto', 'default', '', null, true]) {
    assert.throws(() => compilerSelection(invalid), /pipeline must be off or on/);
  }
});

test('selected entries outside src receive hashes that change with their contents', () => {
  mkdirSync(LOCAL, { recursive: true });
  const directory = mkdtempSync(path.join(LOCAL, 'entry-hash-'));
  const file = path.join(directory, 'compile.bend');
  const entry = path.relative(ROOT, file);
  try {
    writeFileSync(file, 'before');
    assert.deepEqual(entryHashes([entry, entry]), { [entry]: hash('before') });
    writeFileSync(file, 'after');
    assert.deepEqual(entryHashes([entry]), { [entry]: hash('after') });
    assert.throws(() => entryHashes([`${entry}.missing`]), /ENOENT/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});

test('suite literals are domain-checked and cannot replace independent expectations', () => {
  assert.equal(expectedResult('known', 1, undefined), 1);
  assert.equal(expectedResult('off', 0, undefined), 0);
  assert.equal(expectedResult('recorded', 1, 1), 1);
  assert.equal(expectedResult('generated', undefined, 1), 1);
  assert.equal(expectedResult('unrecorded', undefined, undefined), null);
  assert.throws(() => expectedResult('conflict', 0, 1), /disagrees with the recorded oracle/);
  for (const invalid of [-1, 256, 1.5, '1', null, Number.NaN]) {
    assert.throws(() => expectedResult('bad', invalid, undefined), /enum ordinal/);
  }
});
