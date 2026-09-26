#!/usr/bin/env node
// Offline CLI integration check. Stub probabilities are never calibration data.
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { main } from '../node_modules/@lakeday/perch/dist/cli.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const names = [
  'law-domain-inhabited', 'law-observable-essence',
  'law-public-contract-coverage', 'law-independent-model',
  'law-state-composition', 'law-boundaries-and-exhaustion',
  'law-mutation-sensitivity', 'law-proof-claim-integrity',
];
const dir = await mkdtemp(join(tmpdir(), 'knot-law-rules-'));
const previous = process.cwd();
const realFetch = globalThis.fetch;
let verdict = 1;
let calls = [];
globalThis.fetch = async (url, options) => {
  assert.equal(String(url), 'https://api.typesafe.ai/v1/systemone');
  const body = JSON.parse(options.body);
  calls.push(body);
  return { ok: true, json: async () => ({ model: 'offline-wiring-only', answers:
    Object.fromEntries(Object.entries(body.questions).map(([key, question]) => {
      assert.equal(question.type, 'noul');
      return [key, { noul: verdict }];
    })) }) };
};
async function run(args) {
  const output = [], errors = [];
  const code = await main(args, { env: { PERCH_API_KEY: 'offline-wiring-only' },
    stdout: text => output.push(text), stderr: text => errors.push(text) });
  return { code, output: output.join('\n'), errors: errors.join('\n') };
}
try {
  await mkdir(join(dir, '.perch/rules'), { recursive: true });
  await cp(join(root, '.perch/rules/laws.yaml'), join(dir, '.perch/rules/laws.yaml'));
  await writeFile(join(dir, 'perch.yaml'), 'rules: []\n');
  const paths = [
    'packages/probe/LAW_REVIEW.md',
    'packages/probe/family/LAW_REVIEW.md',
    'tests/perch-laws/probe/LAW_REVIEW.md',
    'research/probe/LAW_REVIEW.md',
    'docs/LAW_REVIEW.md',
  ];
  for (const path of paths) {
    await mkdir(dirname(join(dir, path)), { recursive: true });
    await writeFile(join(dir, path), '# Offline wiring probe\nNo behavioral claim.\n');
  }
  process.chdir(dir);
  execFileSync('git', ['init', '-q', '-b', 'main']);
  execFileSync('git', ['add', '.']);
  execFileSync('git', ['-c', 'user.name=Law rule fixture',
    '-c', 'user.email=fixture@example.invalid', '-c', 'core.hooksPath=/dev/null',
    '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Offline rule wiring fixture']);
  const listed = await run(['rules', 'list', '--json']);
  assert.equal(listed.code, 0, listed.errors);
  const laws = JSON.parse(listed.output).filter(rule => rule.from !== 'perch');
  assert.deepEqual(laws.map(rule => rule.name).sort(), [...names].sort());
  assert.ok(laws.every(rule => rule.each === 'file' && !rule.disabled));
  for (const path of paths.slice(0, 4)) {
    calls = [];
    const result = await run(['check', path, '--rules', names.join(','), '--json']);
    assert.equal(result.code, 0, result.errors);
    assert.equal(JSON.parse(result.output).checked, 8);
    assert.equal(calls.length, 1);
    assert.equal(Object.keys(calls[0].questions).length, 8);
  }
  calls = []; verdict = 0;
  const failing = await run(['check', paths[0], '--rules', names[0], '--json']);
  assert.equal(failing.code, 3, failing.errors);
  assert.equal(JSON.parse(failing.output).checked, 1);
  assert.equal(JSON.parse(failing.output).broken.length, 1);
  assert.equal(calls.length, 1);
  calls = [];
  const unrelated = await run(['check', paths[4], '--rules', names.join(','), '--json']);
  assert.equal(unrelated.code, 0, unrelated.errors);
  assert.equal(JSON.parse(unrelated.output).checked, 0);
  assert.equal(calls.length, 0);
  const controls = JSON.parse(await readFile(join(root, 'tests/perch-laws/cases.json'), 'utf8'));
  for (const name of names) {
    const selected = controls.filter(c => c.rule === name);
    assert.deepEqual(selected.map(c => c.split).sort(), ['broken', 'clean', 'held-out']);
    assert.ok(selected.every(c => typeof c.packet === 'string' && c.packet.length > 80));
  }
  console.log('PASS: eight law rules; package/family/control packet coverage; one request per packet; named filtering; advisory finding exit 3; unrelated path excluded; controls present.');
  console.log('No provider contacted. This verifies wiring, not model accuracy or law completeness.');
} finally {
  globalThis.fetch = realFetch;
  process.chdir(previous);
  await rm(dir, { recursive: true, force: true });
}
