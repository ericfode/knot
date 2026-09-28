import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export const config = JSON.parse(await readFile(new URL('../../perch-style.json', import.meta.url), 'utf8'));
export const contract = 'Return the successor of an unsigned word modulo its range.';
export const sources = {
  'z.bend': 'import Base\nimport ./a.bend as A\ndef solve(x: U32) -> U32: A.next(x)\n',
  'a.bend': 'import Base\ndef next(x: U32) -> U32: U32.add(x,1)\n',
  'm.bend': 'import Base\ndef identity(x: U32) -> U32: x\n',
};
export const manifest = { schema: 1, groups: [
  { name: 'successor', files: ['z.bend', 'm.bend'], task: 'contract.md', notes: 'Reading order starts with the public operation.' },
  { name: 'primitive', files: ['a.bend'], task: 'contract.md' },
] };
export const sha = value => createHash('sha256').update(value).digest('hex');

export async function fixture(t, extra = {}) {
  const root = await mkdtemp(join(tmpdir(), 'perch-manifest-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const files = { 'perch-style.json': JSON.stringify(config), ...sources,
    'contract.md': contract, 'manifest.json': JSON.stringify(manifest), ...extra };
  for (const [path, source] of Object.entries(files)) await writeFile(join(root, path), source);
  return root;
}

export function provider(hook = () => {}) {
  const requests = [];
  return { requests, fetchImpl: async (_url, options) => {
    requests.push(options.body);
    const request = JSON.parse(options.body);
    const answers = Object.fromEntries(Object.entries(request.questions).map(([id, q]) => {
      const level = ['potential_profundity', 'criticality', 'style_role'].includes(id) ? 0 : 3;
      return [id, { type: 'score', score: level, confidence: 1,
        probabilities: Object.fromEntries(q.criteria.map((_, i) => [i, Number(i === level)])) }];
    }));
    const body = { model: 'offline-manifest-fixture', answers };
    await hook(request, body, requests.length);
    return { ok: true, json: async () => body };
  } };
}

export async function run(tool, root, args, p = provider(), extra = {}) {
  const output = [], errors = [];
  const code = await tool(['--json', ...args], { root,
    env: { PERCH_API_KEY: 'offline-fixture-only', PERCH_MODEL_ID: 'fixed-fixture' },
    fetchImpl: p.fetchImpl, stdout: line => output.push(line), stderr: line => errors.push(line), ...extra });
  return { code, report: JSON.parse(output[0]), output: output[0], errors, requests: p.requests };
}

function stableReport(value) {
  // Receipt timestamps and measured durations are intentionally nondeterministic.
  if (Array.isArray(value)) return value.map(stableReport);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
    .filter(([key]) => !['at', 'elapsed_ms', 'timings'].includes(key))
    .map(([key, item]) => [key, stableReport(item)]));
  return value;
}

export async function legacyEvidence(tool, root) {
  execFileSync('git', ['init', '-q'], { cwd: root });
  const evidence = {};
  for (const [name, selection] of Object.entries({ declarations: ['z.bend::solve', 'm.bend::identity'],
    files: ['z.bend', 'm.bend'], project: ['--all'] })) {
    const args = ['--task=contract.md', ...selection];
    const preflight = await run(tool, root, ['--preflight', ...args]);
    const live = await run(tool, root, ['--live', '--jobs=1', ...args]);
    evidence[name] = { preflight_exit: preflight.code, preflight_bytes_sha256: sha(preflight.output),
      live_exit: live.code, live_stable_bytes_sha256: sha(JSON.stringify(stableReport(live.report))),
      request_bytes_sha256: live.requests.map(sha) };
  }
  return evidence;
}
