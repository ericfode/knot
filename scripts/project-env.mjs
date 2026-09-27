// Credentials live once, at the Git root of the main checkout. Linked worktrees
// (the app's .claude/worktrees/*, Codex's .codex/worktrees/*) carry no .env of
// their own, so the npm wrappers resolve the shared file instead of copying it.
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

/** A worktree-local .env wins; otherwise the main checkout's .env; otherwise null. */
export function resolveEnvFile(root = ROOT) {
  const local = resolve(root, '.env');
  if (existsSync(local)) return { path: local, source: 'checkout' };
  try {
    const common = execFileSync('git', ['rev-parse', '--path-format=absolute', '--git-common-dir'],
      { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    const mainRoot = dirname(common), shared = resolve(mainRoot, '.env');
    if (mainRoot !== resolve(root) && existsSync(shared)) return { path: shared, source: 'shared-checkout' };
  } catch { /* not a repository, or git too old for --path-format */ }
  return null;
}

/** Load the resolved .env without overriding variables already exported. */
export function loadProjectEnv(root = ROOT, target = process) {
  const found = resolveEnvFile(root);
  if (found) target.loadEnvFile(found.path);
  return found;
}
