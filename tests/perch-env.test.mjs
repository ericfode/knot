import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { realpathSync } from 'node:fs';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { loadProjectEnv, resolveEnvFile } from '../scripts/perch-style.mjs';

// Credentials live once, at the main checkout's Git root; linked worktrees find them there.
const git = (cwd, ...args) => execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();

async function repository(t) {
  // git reports real paths; macOS temp directories are symlinked through /private.
  const base = realpathSync(await mkdtemp(join(tmpdir(), 'perch-env-')));
  const main = join(base, 'main'), worktree = join(base, 'worktree');
  t.after(() => rm(base, { recursive: true, force: true }));
  execFileSync('git', ['init', '--quiet', main]);
  git(main, 'config', 'user.email', 'fixture@example.invalid');
  git(main, 'config', 'user.name', 'Fixture');
  await writeFile(join(main, 'README.md'), 'fixture\n');
  git(main, 'add', 'README.md');
  git(main, 'commit', '--quiet', '-m', 'fixture');
  git(main, 'worktree', 'add', '--quiet', worktree, '-b', 'linked');
  return { main, worktree };
}

test('a linked worktree without .env resolves the main checkout credential file; a local .env wins; none yields null', async t => {
  const { main, worktree } = await repository(t);
  assert.equal(resolveEnvFile(worktree), null);
  assert.equal(resolveEnvFile(main), null);
  await writeFile(join(main, '.env'), 'PERCH_API_KEY=offline-fixture-not-a-real-key\n', { mode: 0o600 });
  assert.deepEqual(resolveEnvFile(main), { path: join(main, '.env'), source: 'checkout' });
  assert.deepEqual(resolveEnvFile(worktree), { path: join(main, '.env'), source: 'shared-checkout' });
  await writeFile(join(worktree, '.env'), 'PERCH_API_KEY=worktree-local-fixture\n', { mode: 0o600 });
  assert.deepEqual(resolveEnvFile(worktree), { path: join(worktree, '.env'), source: 'checkout' });
});

test('loading uses the resolved file exactly once and reports where it came from', async t => {
  const { main, worktree } = await repository(t);
  await writeFile(join(main, '.env'), 'PERCH_API_KEY=offline-fixture-not-a-real-key\n', { mode: 0o600 });
  const loaded = [];
  const found = loadProjectEnv(worktree, { loadEnvFile: path => loaded.push(path) });
  assert.deepEqual(loaded, [join(main, '.env')]);
  assert.equal(found.source, 'shared-checkout');
  const none = realpathSync(await mkdtemp(join(tmpdir(), 'perch-env-none-')));
  t.after(() => rm(none, { recursive: true, force: true }));
  assert.equal(loadProjectEnv(none, { loadEnvFile: path => loaded.push(path) }), null);
  assert.equal(loaded.length, 1, 'no credential file means no load attempt');
});
