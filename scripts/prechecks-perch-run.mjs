#!/usr/bin/env node
// The live half of the prechecks Perch rules. Run it from the MAIN checkout, where the credentials are, and only
// after the offline packets exist (`npm run -s prechecks:packets -- --repo <worktree> --out <dir>`).
//
//   node scripts/prechecks-perch-run.mjs                  # dry run (the default): what would be asked, zero requests
//   node scripts/prechecks-perch-run.mjs --controls       # dry run of the calibration set
//   node scripts/prechecks-perch-run.mjs --live [--controls] [--rules a,b] [--packets DIR] [--cap 40] [--out FILE]
//
// Live mode asks Perch one question per packet through the retained-receipt wrapper (scripts/perch-workflow.mjs), so
// the run is recorded under .perch/usage/. It refuses to run in a linked worktree, stops on the first authentication
// or quota failure instead of retrying, and never reads a dotenv file itself. Verdicts stay advisory (gate: false):
// confirm any suspected defect deterministically before changing code (AGENTS.md), and record calibration runs in
// docs/perch-review-log.md. A stub or dry-run result is never calibration.
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { cp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const RULES = [
  'claim-holds-against-evidence', 'passages-agree', 'outcome-follows-d4', 'clause-vs-delta',
  'expectation-independent', 'kill-is-semantic', 'required-laws-met',
];
const FLOOR = 0.8;

async function walk(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true }).catch(() => [])) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await walk(path));
    else if (entry.name.endsWith('.md')) found.push(path);
  }
  return found.sort();
}

/** Stage the tracked calibration set as one packet per directory, in the layout the rules select. */
export async function stageControls(root, target, source = ROOT) {
  const cases = JSON.parse(await readFile(join(source, 'tests/prechecks/perch-controls/cases.json'), 'utf8'));
  const scratch = resolve(target);
  if (!scratch.startsWith(resolve(root, '.local') + sep) || !/controls/.test(basename(scratch))) {
    throw new Error(`Refusing to stage controls into ${target}: it must be a controls directory below .local/`);
  }
  await rm(scratch, { recursive: true, force: true });
  for (const item of cases.cases) {
    const destination = join(target, `${item.split}-${item.id}`, item.rule, '0001.md');
    await mkdir(dirname(destination), { recursive: true });
    await cp(join(source, 'tests/prechecks/perch-controls', item.packet), destination);
  }
  return cases.cases;
}

/** The packets a run would ask about: {path, rule, group}, at most `cap` per <increment>/<head8> group. */
export async function plan({ root = ROOT, packets = '.local/prechecks/packets', rules = RULES, cap = 40, controls = false, controlsRoot = ROOT } = {}) {
  const base = resolve(root, packets);
  const expected = controls ? await stageControls(root, base, controlsRoot) : null;
  const rows = [], counts = new Map();
  for (const file of await walk(base)) {
    const parts = relative(base, file).split('/');
    const rule = parts.at(-2);
    if (!rules.includes(rule)) continue;
    const group = controls ? parts[0] : parts.slice(0, 2).join('/');
    counts.set(group, (counts.get(group) ?? 0) + 1);
    if (!controls && counts.get(group) > cap) continue;
    const label = controls ? expected.find(c => `${c.split}-${c.id}` === parts[0]) : null;
    rows.push({ path: relative(root, file), rule, group, expected: label?.expected ?? null, split: label?.split ?? null });
  }
  return rows;
}

function mainCheckout(root) {
  const git = args => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();
  return resolve(root, git(['rev-parse', '--git-dir'])) === resolve(root, git(['rev-parse', '--git-common-dir']));
}

export function separation(results) {
  const judged = results.filter(r => r.expected && typeof r.probability_broken === 'number');
  if (!judged.length) return null;
  const wrong = judged.filter(r => (r.expected === 'broken') !== (r.probability_broken >= FLOOR));
  return { floor: FLOOR, judged: judged.length, misclassified: wrong.map(r => r.path), separates: wrong.length === 0 };
}

/**
 * Ask Perch about each planned packet. `run` is scripts/perch-workflow.mjs's runPerch (injectable for offline tests).
 */
export async function execute(rows, { root = ROOT, env = process.env, live = false, requireMain = true, run = null } = {}) {
  if (!live) return { live: false, requests: 0, results: rows.map(r => ({ ...r, status: 'planned' })) };
  if (requireMain && !mainCheckout(root)) {
    throw new Error('Live runs belong to the main checkout (the credentials are there); this is a linked worktree.');
  }
  if (!env.PERCH_API_KEY && !env.TYPESAFE_API_KEY && !existsSync(join(root, '.env'))) {
    throw new Error('No Perch credential in the environment and no .env in this checkout; run from the main checkout.');
  }
  const runPerch = run ?? (await import('./perch-workflow.mjs')).runPerch;
  const results = [];
  for (const row of rows) {
    const output = [], errors = [];
    const code = await runPerch(['check', row.path, '--rules', row.rule, '--json'],
      { root, env, stdout: text => output.push(text), stderr: text => errors.push(text) });
    let parsed = null;
    try { parsed = JSON.parse(output.join('\n')); } catch { /* recorded as unreadable */ }
    // A file check reports one unit at the top level; a directory check reports an array of units.
    const units = Array.isArray(parsed) ? parsed : parsed?.units ?? (parsed ? [parsed] : []);
    const asked = units.flatMap(unit => unit.asked ?? []).find(a => a.rule === row.rule);
    const result = { ...row, exit: code, checked: parsed?.checked ?? units[0]?.checked ?? null,
      probability_broken: typeof asked?.broken === 'number' ? asked.broken : null,
      floor: asked?.floor ?? null, status: code === 0 ? 'clean' : code === 3 ? 'flagged' : 'failed' };
    if (code !== 0 && code !== 3) result.error = errors.join(' ').slice(0, 200);
    results.push(result);
    if (result.status === 'failed' && /PERCH_API_KEY is not set|unauthor|401|402|403|429|quota|credit/i.test(errors.join(' '))) {
      results.push({ path: null, status: 'stopped', error: 'authentication or quota failure; not retried' });
      break;
    }
  }
  return { live: true, requests: results.filter(r => r.checked !== undefined && r.status !== 'stopped').length, results };
}

async function cli(argv) {
  const value = flag => { const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : undefined; };
  const live = argv.includes('--live'), controls = argv.includes('--controls');
  const rules = value('--rules')?.split(',') ?? RULES;
  const bad = rules.filter(r => !RULES.includes(r));
  if (bad.length) throw new Error(`Unknown rule: ${bad.join(', ')}`);
  const packets = value('--packets') ?? (controls ? '.local/prechecks/packets/controls' : '.local/prechecks/packets');
  const rows = await plan({ root: ROOT, packets, rules, cap: Number(value('--cap') ?? 40), controls });
  console.log(`${live ? 'LIVE' : 'DRY RUN'}: ${rows.length} packet(s) across ${new Set(rows.map(r => r.rule)).size} rule(s) from ${packets}`);
  for (const rule of RULES) {
    const n = rows.filter(r => r.rule === rule).length;
    if (n) console.log(`  ${rule.padEnd(30)} ${n}`);
  }
  if (!live) { console.log('No request was made. Add --live to ask Perch (main checkout only).'); return 0; }
  const report = await execute(rows, { root: ROOT, live: true });
  const summary = { ...report, separation: separation(report.results), at: new Date().toISOString() };
  const out = resolve(ROOT, value('--out') ?? `.local/prechecks/perch-run-${summary.at.replaceAll(':', '-')}.json`);
  await mkdir(dirname(out), { recursive: true });
  await writeFile(out, JSON.stringify(summary, null, 2) + '\n');
  for (const r of report.results) console.log(`  ${String(r.status).padEnd(8)} ${r.probability_broken ?? '-'} ${r.path ?? r.error}`);
  console.log(`Report: ${relative(ROOT, out)}. Verdicts are advisory; record calibration in docs/perch-review-log.md.`);
  return report.results.some(r => r.status === 'failed' || r.status === 'stopped') ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  cli(process.argv.slice(2)).then(code => { process.exitCode = code; },
    error => { console.error(`prechecks-perch-run: ${error.message}`); process.exitCode = 2; });
}
