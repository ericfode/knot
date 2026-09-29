import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const original = await readFile(new URL('../scripts/perch-context-interfaces.mjs', import.meta.url), 'utf8');
const mutants = [
  { name: 'summary-leaks-body', witness: 'definition interfaces keep nested',
    from: "const head = Buffer.from(text).subarray(0, end).toString('utf8');", to: 'const head = text;' },
  { name: 'unverified-package-accepted', witness: 'tampered unused package member',
    from: "if (actualHash !== id) throw failure('package-hash-mismatch');", to: 'void actualHash;' },
  { name: 'truncation-marker-dropped', witness: 'datatype byte exhaustion',
    from: "if (reason === 'context-byte-limit') truncated = true;", to: "if (reason === 'context-byte-limit') truncated = false;" },
  { name: 'group-silently-over-bound', witness: 'composition exact UTF-8 bound',
    from: 'const over = bytes > config.potential_profundity.max_composition_bytes;', to: 'const over = false;' },
  { name: 'store-path-in-identity', witness: 'package identity and composition state',
    from: 'const path = `${id}/${row.path}`;', to: 'const path = actual;' },
  { name: 'anti-anchoring-omitted', witness: 'interface instruction retains',
    from: ' Do not infer a potential verdict, previous scores or missing implementation.', to: '' },
  { name: 'binder-colon-truncates-head', witness: 'dependent signature dependencies',
    from: 'const end = declaration.body_start?.byte - declaration.location.start.byte;',
    to: "const end = text.indexOf(':', text.indexOf('->')) + 1;" },
  { name: 'default-store-omitted', witness: 'default candidate store verifies',
    from: "resolve(root, explicitStore ?? process.env.BEND_LIB ?? resolve(homedir(), '.bend/lib'))",
    to: "resolve(root, explicitStore ?? 'no-default-store')" },
  { name: 'names-only-marker-dropped', witness: 'marks every cut',
    from: 'notes.names_only = { count: (notes.names_only?.count ?? 0) + 1, note: NAMES_ONLY_NOTE };', to: 'void notes;' },
  { name: 'primary-source-shortened', witness: 'never shortens the primary source',
    from: 'throw new Error(tooLarge(prefix, context, maxBytes));', to: 'prefix.source = prefix.source.slice(0, maxBytes >> 1);' },
  { name: 'names-only-tier-skipped', witness: 'fits a state the interface tier cannot',
    from: 'for (const { item } of cuts) {', to: 'for (const { item } of []) {' },
  { name: 'names-only-order-nondeterministic', witness: 'largest saving, then path, then name',
    from: 'cuts.sort(largestSavingFirst);', to: 'cuts.sort((a, b) => b.saving - a.saving);' },
  { name: 'names-only-row-not-recorded', witness: 'also cuts a body the interface tier kept',
    from: 'if (row) row.reason = NAMES_ONLY_REASON; else summarized.push({ path: item.path, name: item.name, reason: NAMES_ONLY_REASON });',
    to: 'void row;' },
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
    fileURLToPath(new URL('./perch-context.test.mjs', import.meta.url))], { env, encoding: 'utf8', timeout: 30000 });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout, /ERR_ASSERTION/);
  assert.match(result.stdout, /# fail 1\n/);
  assert.doesNotMatch(result.stderr, /SyntaxError|ERR_MODULE_NOT_FOUND/);
});
