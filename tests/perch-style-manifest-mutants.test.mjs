import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const tool = new URL('../scripts/perch-style.mjs', import.meta.url);
const original = await readFile(tool, 'utf8');
const mutants = [
  { name: 'lexical-order', witness: 'manifest composition follows reading order then collaborators',
    from: "const selected = readingOrder ?? [...new Set(candidates.map(c => c.path ?? c.target.split('::')[0]))].sort();",
    to: "const selected = [...new Set(candidates.map(c => c.path ?? c.target.split('::')[0]))].sort();" },
  { name: 'any-group-qualifies', witness: 'manifest qualification requires every group',
    from: 'groups.every(group => group.qualification.fully_qualified)',
    to: 'groups.some(group => group.qualification.fully_qualified)' },
  { name: 'filtered-is-complete', witness: 'filtered qualification cannot claim the entire manifest',
    from: 'manifest_fully_qualified: qualified && groupName === undefined',
    to: 'manifest_fully_qualified: qualified' },
  { name: 'ignore-final-freshness', witness: 'later groups cannot hide stale earlier sources',
    from: 'const changed_sources = await changedStyleSources(watched, root);',
    to: 'const changed_sources = [];' },
];

for (const mutant of mutants) test(`semantic mutant killed: ${mutant.name}`, async t => {
  assert.equal(original.split(mutant.from).length, 2, 'mutation must have one exact site');
  const directory = await mkdtemp(join(tmpdir(), 'perch-manifest-mutant-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  // The mutant imports the unchanged dependencies. Relative runtime reads of
  // the context contract retain their original bytes as well.
  const source = original.replace(mutant.from, mutant.to)
    .replace(/from '(\.[^']+)'/g, (_, path) => `from '${new URL(path, tool).href}'`);
  const path = join(directory, 'perch-style.mjs');
  await writeFile(path, source);
  await symlink(fileURLToPath(new URL('../scripts/perch-bend-context.mjs', import.meta.url)), join(directory, 'perch-bend-context.mjs'));
  execFileSync(process.execPath, ['--check', path]);
  const env = { ...process.env, KNOT_STYLE_TEST_MODULE: pathToFileURL(path).href };
  delete env.NODE_TEST_CONTEXT;
  const result = spawnSync(process.execPath, ['--test', `--test-name-pattern=${mutant.witness}`,
    fileURLToPath(new URL('./perch-style-manifest.test.mjs', import.meta.url))], {
    encoding: 'utf8', timeout: 30000,
    env,
  });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout, /ERR_ASSERTION/, 'the unchanged behavioral assertion must kill the mutant');
  assert.match(result.stdout, /# fail 1\n/);
  assert.doesNotMatch(result.stderr, /SyntaxError|ERR_MODULE_NOT_FOUND/);
});
