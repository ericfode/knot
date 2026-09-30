import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { gunzipSync } from 'node:zlib';
import { receiptJSON } from '../lib/receipt.mjs';
import { ROOT } from '../lib/system.mjs';

test('relocated receipts retain observations and have the same portable paths', () => {
  const record = ({ root, toolchain, library, node }) => ({
    argv: [node, `${root}/bench/run.mjs`, `${toolchain}/bend/main.ts`, `${library}/0xabc/main.bend`],
    path: `${root}/.local/bench/runs/record/main.wasm`,
    stdout: JSON.stringify({ path: `${root}/.local/bench/runs/record/main.wasm`, result: 1 }),
    nested: { base: `${root}/.toolchain/bend/base.bend`, exit: 0, samples: [1.25, 2.5], sha256: 'a'.repeat(64) },
  });
  const left = { root: '/work/alice/knot', toolchain: '/cache/alice/seed', library: '/cache/alice/lib', node: '/tools/alice/node' };
  const right = { root: '/work/bob/knot with spaces', toolchain: '/cache/bob/seed', library: '/cache/bob/lib', node: '/tools/bob/node' };
  const input = record(left), unchanged = structuredClone(input);
  const expected = {
    argv: ['$NODE', '$ROOT/bench/run.mjs', '.toolchain/bend/main.ts', '$BEND_LIB/0xabc/main.bend'],
    path: '$ROOT/.local/bench/runs/record/main.wasm',
    stdout: '{"path":"$ROOT/.local/bench/runs/record/main.wasm","result":1}',
    nested: { base: '.toolchain/bend/base.bend', exit: 0, samples: [1.25, 2.5], sha256: 'a'.repeat(64) },
  };
  assert.deepEqual(JSON.parse(receiptJSON(input, left)), expected);
  assert.equal(receiptJSON(input, left), receiptJSON(record(right), right));
  assert.deepEqual(input, unchanged, 'serialization must not change executable paths in memory');
  assert.equal(receiptJSON(expected, left), receiptJSON(input, left), 'normalization must be idempotent');
});

test('gate completion paths name the exported tree without its temporary directory', () => {
  const options = { root: '/work/knot', toolchain: '/cache/seed', library: '/cache/lib', node: '/tools/node' };
  for (const root of [options.root, '$WORKTREE', '$ROOT']) {
    assert.deepEqual(JSON.parse(receiptJSON({
      completion: `7 mutants; ${root}/.local/gates/run-abc123/worktree/tests/compiler-checker/receipts/checker.json`,
    }, options)), { completion: '7 mutants; $ROOT/tests/compiler-checker/receipts/checker.json' });
  }
});

test('path prefix matching leaves sibling paths and non-path observations intact', () => {
  const options = { root: '/work/knot', toolchain: '/cache/seed', library: '/cache/lib', node: '/tools/node' };
  const input = { message: 'failure (/work/knot/src/parse.bend): Invalid',
    sibling: '/work/knot-other/src/parse.bend', embedded: '/another/work/knot/src/parse.bend',
    word: 'name/work/knot/src/parse.bend', numeric: 42, sourceHash: 'b'.repeat(64) };
  assert.deepEqual(JSON.parse(receiptJSON(input, options)), {
    ...input, message: 'failure ($ROOT/src/parse.bend): Invalid',
  });
});

test('all committed benchmark receipts are free of C4 host-path tokens', () => {
  // Match the independent precheck, including the temporary gate-export suffix
  // that remains host-specific even after a checkout-prefix substitution.
  const hostPath = /\/Users\/|\/home\/[^/\s"']+\/|\/private\/(?:tmp|var)|\/var\/folders|[.]claude\/worktrees|[.]local\/gates\/run-|(?:[.][.]\/){2,}[.]toolchain/;
  const directory = path.join(ROOT, 'bench/receipts');
  for (const name of readdirSync(directory, { recursive: true }).filter(name => /\.json(?:\.gz)?$/.test(name))) {
    const raw = readFileSync(path.join(directory, name));
    const text = (name.endsWith('.gz') ? gunzipSync(raw) : raw).toString('utf8');
    JSON.parse(text);
    assert.doesNotMatch(text, hostPath, name);
  }
});
