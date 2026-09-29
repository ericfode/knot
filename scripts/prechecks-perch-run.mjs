#!/usr/bin/env node
// The live half of the prechecks Perch rules. Run it from the MAIN checkout, where the credentials are, and only
// after the offline packets exist (`npm run -s prechecks:packets -- --repo <worktree> --out <dir>`).
//
//   node scripts/prechecks-perch-run.mjs                  # dry run (the default): what would be asked, zero requests
//   node scripts/prechecks-perch-run.mjs --controls       # dry run of the calibration set
//   node scripts/prechecks-perch-run.mjs --live [--controls [--split dev|held-out]] [--rules a,b] [--packets DIR] [--cap 40] [--out FILE]
//
// Live mode asks Perch one question per packet through the retained-receipt wrapper (scripts/perch-workflow.mjs), so
// the run is recorded under .perch/usage/. It refuses to run in a linked worktree, stops on the first authentication
// or quota failure instead of retrying, and never reads a dotenv file itself. Verdicts stay advisory (gate: false):
// confirm any suspected defect deterministically before changing code (AGENTS.md), and record calibration runs in
// docs/perch-review-log.md. A stub or dry-run result is never calibration.
//
// What is asked. The rules select packets only below `.local/prechecks/packets/**/<rule>/*.md` of this checkout, so a
// packet directory built elsewhere (`--packets DIR`, a worktree's, a `--out` of any name) is copied into
// `.local/prechecks/packets/staged/` before it is asked, and the dry run says so. The cap is per rule and per
// (increment, head) read from each packet's own header, never from directory depth, and it is the number the packet builder
// stops at (scripts/prechecks/packets/limits.json): a run that builds and asks with the defaults asks every packet, and
// anything it skips is printed by rule. Staged calibration controls and staged copies are asked only by the run that
// staged them; the controls are removed after a live calibration run.
//
// Calibration. `--split dev` asks only the dev controls (splits `broken` and `clean`), which tune a rule; `--split held-out`
// asks only the held-out ones, once, after the rule text is frozen. A packet is flagged when its probability is strictly
// above its rule's floor (`min` in the rules file, as Perch reports it), and a rule separates when every expected-broken
// control is flagged and no expected-clean one is.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { cp, mkdir, open, readdir, readFile, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const RULES = [
  'claim-holds-against-evidence', 'passages-agree', 'outcome-follows-d4', 'clause-vs-delta',
  'expectation-independent', 'kill-is-semantic', 'required-laws-met',
];
export const PACKET_ROOT = '.local/prechecks/packets';
export const CAP = JSON.parse(readFileSync(join(ROOT, 'scripts/prechecks/packets/limits.json'), 'utf8')).packets_per_rule_per_head;
const FLOOR = 0.8;                    // only when Perch reports no floor for a result
export const SPLITS = { dev: ['broken', 'clean'], 'held-out': ['held-out'] };
const HEADER = /^<!-- prechecks packet v\d+; rule=([a-z0-9-]+); increment=([^;]+); head=([^;]+);/;
const SIDE_ROOTS = ['controls', 'staged'];

async function walk(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true }).catch(() => [])) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await walk(path));
    else if (entry.name.endsWith('.md')) found.push(path);
  }
  return found.sort();
}

/** The (rule, increment, head) a packet names in its own header, or null when it has none. */
export async function readHeader(file) {
  const handle = await open(file, 'r');
  try {
    const { buffer, bytesRead } = await handle.read(Buffer.alloc(1024), 0, 1024, 0);
    const match = HEADER.exec(buffer.toString('utf8', 0, bytesRead).split('\n')[0]);
    return match ? { rule: match[1], increment: match[2], head: match[3] } : null;
  } finally {
    await handle.close();
  }
}

/** True when the rules' `where` glob (`.local/prechecks/packets/**\/<rule>/*.md`) selects this repo-relative path. */
export function inWhere(relPath, rule) {
  const parts = relPath.split(sep);
  return relPath.startsWith(PACKET_ROOT + sep) && !parts.includes('..') && parts.at(-2) === rule && parts.at(-1).endsWith('.md');
}

function safe(part) { return String(part ?? 'none').replace(/[^\w.+-]/g, '_'); }

function guardControls(root, target) {
  const scratch = resolve(target);
  if (!scratch.startsWith(resolve(root, '.local') + sep) || !/controls/.test(basename(scratch))) {
    throw new Error(`Refusing to stage controls into ${target}: it must be a controls directory below .local/`);
  }
  return scratch;
}

/** Stage the tracked calibration set as one packet per directory, in the layout the rules select. */
export async function stageControls(root, target, source = ROOT) {
  const cases = JSON.parse(await readFile(join(source, 'tests/prechecks/perch-controls/cases.json'), 'utf8'));
  const scratch = guardControls(root, target);
  await rm(scratch, { recursive: true, force: true });
  for (const item of cases.cases) {
    const destination = join(target, `${item.split}-${item.id}`, item.rule, '0001.md');
    await mkdir(dirname(destination), { recursive: true });
    await cp(join(source, 'tests/prechecks/perch-controls', item.packet), destination);
  }
  return cases.cases;
}

/** Remove what stageControls wrote (the calibration run's own scratch, never the production packets). */
export async function unstageControls(root, target) {
  await rm(guardControls(root, target), { recursive: true, force: true });
}

/**
 * The packets a run would ask about: { rows, skipped, staged }.
 * `rows` are {path, rule, group, increment, head, expected, split, source?}, at most `cap` per rule and per (increment, head)
 * as each packet's header names them. A packet below `packets` that the rules' `where` glob does not select gets a `path`
 * under .local/prechecks/packets/staged/ and a `source`: execute() copies it there before asking. `skipped` counts the packets
 * over the cap by rule, and `staged` counts the packets that need copying.
 */
export async function plan({ root = ROOT, packets = PACKET_ROOT, rules = RULES, cap = CAP, controls = false, controlsRoot = ROOT, split = null } = {}) {
  if (split && !SPLITS[split]) throw new Error(`Unknown split: ${split} (dev or held-out)`);
  if (split && !controls) throw new Error('--split selects calibration controls; add --controls');
  const base = resolve(root, packets);
  const expected = controls ? await stageControls(root, base, controlsRoot) : null;
  const rows = [], counts = new Map(), skipped = {};
  let staged = 0;
  for (const file of await walk(base)) {
    const parts = relative(base, file).split(sep);
    const rule = parts.at(-2);
    if (!rules.includes(rule)) continue;
    if (!controls && SIDE_ROOTS.includes(parts[0]) && parts.length > 2) continue;
    const header = await readHeader(file);
    const increment = header?.increment ?? parts[0], head = header?.head ?? parts[1] ?? 'unknown';
    const group = controls ? parts[0] : `${increment}/${head}/${rule}`;
    counts.set(group, (counts.get(group) ?? 0) + 1);
    if (!controls && counts.get(group) > cap) { skipped[rule] = (skipped[rule] ?? 0) + 1; continue; }
    const label = controls ? expected.find(c => `${c.split}-${c.id}` === parts[0]) : null;
    if (split && !SPLITS[split].includes(label?.split)) continue;
    let path = relative(root, file), source;
    if (!inWhere(path, rule)) {
      const tag = createHash('sha1').update(file).digest('hex').slice(0, 6);
      path = join(PACKET_ROOT, 'staged', safe(increment), safe(head), rule, `${tag}-${basename(file)}`);
      source = file;
      staged += 1;
    }
    rows.push({ path, rule, group, increment, head, expected: label?.expected ?? null, split: label?.split ?? null, ...(source ? { source } : {}) });
  }
  return { rows, skipped, staged };
}

function mainCheckout(root) {
  const git = args => execFileSync('git', ['-C', root, ...args], { encoding: 'utf8' }).trim();
  return resolve(root, git(['rev-parse', '--git-dir'])) === resolve(root, git(['rev-parse', '--git-common-dir']));
}

/** Perch flags a verdict strictly above the rule's floor (floorFor in Perch's CLI). */
export const flaggedAt = r => r.probability_broken > (r.floor ?? FLOOR);

export function separation(results) {
  const judged = results.filter(r => r.expected && typeof r.probability_broken === 'number');
  if (!judged.length) return null;
  const wrong = judged.filter(r => (r.expected === 'broken') !== flaggedAt(r));
  const rules = {};
  for (const r of judged) {
    const rule = rules[r.rule] ??= { floor: r.floor ?? FLOOR, broken: [], clean: [] };
    rule[r.expected].push(r.probability_broken);
  }
  for (const rule of Object.values(rules)) {
    rule.broken.sort((a, b) => a - b); rule.clean.sort((a, b) => a - b);
    rule.separates = rule.broken.every(p => p > rule.floor) && rule.clean.every(p => p <= rule.floor);
  }
  return { judged: judged.length, misclassified: wrong.map(r => r.path), separates: wrong.length === 0, rules };
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
  for (const row of rows) {                                    // a packet outside the rules' where glob is never asked in place
    if (!inWhere(row.path, row.rule) && !row.source) {
      throw new Error(`Refusing ${row.path}: no rule reads it (rules select ${PACKET_ROOT}/**/<rule>/*.md) and it has no source to stage`);
    }
    if (row.source) {
      await mkdir(dirname(join(root, row.path)), { recursive: true });
      await cp(row.source, join(root, row.path));
    }
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
  const packets = value('--packets') ?? (controls ? `${PACKET_ROOT}/controls` : PACKET_ROOT);
  const cap = Number(value('--cap') ?? CAP);
  const split = value('--split') ?? null;
  const { rows, skipped, staged } = await plan({ root: ROOT, packets, rules, cap, controls, split });
  console.log(`${live ? 'LIVE' : 'DRY RUN'}: ${rows.length} packet(s) across ${new Set(rows.map(r => r.rule)).size} rule(s) from ${packets}${split ? ` (${split} controls)` : ''}`);
  for (const rule of RULES) {
    const n = rows.filter(r => r.rule === rule).length;
    if (n || skipped[rule]) console.log(`  ${rule.padEnd(30)} ${String(n).padStart(4)}${skipped[rule] ? `  (${skipped[rule]} skipped over the cap of ${cap} per rule and head)` : ''}`);
  }
  if (staged) console.log(`  ${staged} packet(s) lie outside ${PACKET_ROOT}/**/<rule>/*.md and ${live ? 'are copied' : 'would be copied'} into ${PACKET_ROOT}/staged/ first`);
  if (!live) {
    if (controls) await unstageControls(ROOT, resolve(ROOT, packets));      // a dry run leaves nothing staged behind
    console.log('No request was made. Add --live to ask Perch (main checkout only).');
    return 0;
  }
  try {
    const report = await execute(rows, { root: ROOT, live: true });
    const summary = { ...report, split, skipped, separation: separation(report.results), at: new Date().toISOString() };
    const out = resolve(ROOT, value('--out') ?? `.local/prechecks/perch-run-${summary.at.replaceAll(':', '-')}.json`);
    await mkdir(dirname(out), { recursive: true });
    await writeFile(out, JSON.stringify(summary, null, 2) + '\n');
    for (const r of report.results) console.log(`  ${String(r.status).padEnd(8)} ${r.probability_broken ?? '-'} ${r.expected ?? ''} ${r.path ?? r.error}`);
    for (const [rule, s] of Object.entries(summary.separation?.rules ?? {})) {
      console.log(`  ${rule.padEnd(30)} floor ${s.floor}: broken ${s.broken.join(' ') || '-'} | clean ${s.clean.join(' ') || '-'} | ${s.separates ? 'separates' : 'does not separate'}`);
    }
    console.log(`Report: ${relative(ROOT, out)}. Verdicts are advisory; record calibration in docs/perch-review-log.md.`);
    return report.results.some(r => r.status === 'failed' || r.status === 'stopped') ? 1 : 0;
  } finally {
    if (controls) await unstageControls(ROOT, resolve(ROOT, packets));      // the next production run must not ask the controls again
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  cli(process.argv.slice(2)).then(code => { process.exitCode = code; },
    error => { console.error(`prechecks-perch-run: ${error.message}`); process.exitCode = 2; });
}
