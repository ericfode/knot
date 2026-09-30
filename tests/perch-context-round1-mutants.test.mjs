import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const original = await readFile(new URL('../scripts/perch-context-interfaces.mjs', import.meta.url), 'utf8');
const mutants = [
  { name: 'names-only-summary-order-locale-dependent', witness: 'complete states and hashes agree',
    from: 'const byIdentity = (a, b) => byCode(a.path, b.path) || byCode(a.name, b.name);',
    to: 'const byIdentity = (a, b) => a.path.localeCompare(b.path) || a.name.localeCompare(b.name);' },
  { name: 'names-only-saving-ignores-counters', witness: 'savings include byte counters',
    from: 'const counterSaving = encoded(notes.source_bytes) - encoded(context.provenance.source_bytes - Buffer.byteLength(item.source));',
    to: 'const counterSaving = 0;' },
  { name: 'names-only-tie-break-uses-utf16', witness: 'equal savings compare Unicode scalar',
    from: 'const delta = left[i].codePointAt(0) - right[i].codePointAt(0);',
    to: 'const delta = left[i].charCodeAt(0) - right[i].charCodeAt(0);' },
  { name: 'names-only-required-minimum-skipped', witness: 'seed-accepted datatype boundary',
    from: 'context.provenance.state_metadata = {',
    to: "throw new Error('required minimum fitting skipped');\n  context.provenance.state_metadata = {" },
  { name: 'names-only-contract-omission-unmarked', witness: 'unavoidable contract omissions',
    from: 'context.provenance.truncated = notes.truncated = true;',
    to: 'context.provenance.truncated = notes.truncated = false;' },
];
for (const mutant of mutants) test(`semantic mutant killed: ${mutant.name}`, async t => {
  assert.equal(original.split(mutant.from).length, 2, 'exactly one mutation site');
  const directory = await mkdtemp(join(tmpdir(), 'perch-context-mutant-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const path = join(directory, 'context.mjs');
  await writeFile(path, original.replace(mutant.from, mutant.to));
  execFileSync(process.execPath, ['--check', path]);
  const env = { ...process.env, BEND_NO_TELEMETRY: '1', KNOT_CONTEXT_TEST_MODULE: pathToFileURL(path).href };
  delete env.NODE_TEST_CONTEXT;
  const result = spawnSync(process.execPath, ['--test', `--test-name-pattern=${mutant.witness}`,
    fileURLToPath(new URL('./perch-context-round1.test.mjs', import.meta.url))],
    { env, encoding: 'utf8', timeout: 30000 });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout, /ERR_ASSERTION/);
  assert.match(result.stdout, /# fail 1\n/);
  assert.doesNotMatch(result.stderr, /SyntaxError|ERR_MODULE_NOT_FOUND/);
});
