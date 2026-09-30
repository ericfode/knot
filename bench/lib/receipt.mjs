import { realpathSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROOT } from './system.mjs';

const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Execution keeps real paths. Only the persisted copy uses portable identities;
// samples, diagnostics, input hashes and run identifiers remain observations.
export function receiptJSON(value, {
  root = ROOT,
  toolchain = realpathSync(path.join(ROOT, '.toolchain')),
  library = process.env.BEND_LIB || path.join(os.homedir(), '.bend/lib'),
  node = process.execPath,
} = {}) {
  root = root.replace(/\/$/, '');
  const prefix = '(?<![\\w/.-])';
  const boundary = '(?=/|$|[\\s\'"\\):,])';
  const exported = new RegExp(`${prefix}(?:${escape(root)}|\\$ROOT|\\$WORKTREE)/\\.local/gates/run-[^/\\s\'"]+/worktree${boundary}`, 'g');
  const aliases = [
    [path.join(root, '.toolchain'), '.toolchain'], [toolchain, '.toolchain'],
    [library, '$BEND_LIB'], [node, '$NODE'], [root, '$ROOT'], ['$WORKTREE', '$ROOT'],
  ].sort((a, b) => b[0].length - a[0].length)
    .map(([from, to]) => [new RegExp(`${prefix}${escape(from)}${boundary}`, 'g'), to]);
  return JSON.stringify(value, (_key, item) => {
    if (typeof item !== 'string') return item;
    item = item.replace(exported, () => '$ROOT');
    for (const [pattern, token] of aliases) item = item.replace(pattern, () => token);
    return item;
  }, 2) + '\n';
}
