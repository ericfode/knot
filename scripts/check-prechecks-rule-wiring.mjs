#!/usr/bin/env node
// Offline CLI integration check for .perch/rules/prechecks.yaml. Stub probabilities are never calibration data:
// this proves selection and plumbing, not that any rule separates broken packets from clean ones.
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import YAML from '../node_modules/yaml/dist/index.js';
import { main } from '../node_modules/@lakeday/perch/dist/cli.mjs';
import { CAP, PACKET_ROOT, SPLITS, execute, flaggedAt, inWhere, plan, readHeader, separation, stageControls, unstageControls } from './prechecks-perch-run.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const names = [
  'claim-holds-against-evidence', 'passages-agree', 'outcome-follows-d4', 'clause-vs-delta',
  'expectation-independent', 'kill-is-semantic', 'required-laws-met',
];
// A control's cell: its dev split, or held-out with its expected label. Every rule needs DEV_MIN dev controls of each label;
// a held-out cell may instead be a documented gap.
const cells = ['broken', 'clean', 'held-out/broken', 'held-out/clean'];
const cellOf = c => (c.split === 'held-out' ? `held-out/${c.expected}` : c.split);
const DEV_MIN = 3;
// Every rule is uncalibrated (docs/perch-review-log.md, 2026-09-29): no dev gap reached the 0.10 margin, so each keeps 80.
const FLOORS = Object.fromEntries(names.map(name => [name, 80]));
const RULES_SET = new Set(names);
const dir = await mkdtemp(join(tmpdir(), 'knot-prechecks-rules-'));
const previous = process.cwd();
const realFetch = globalThis.fetch;
let verdict = 1;
let queue = null;                 // per-request verdicts for the runner test; never a calibration
let calls = [];
globalThis.fetch = async (url, options) => {
  assert.equal(String(url), 'https://api.typesafe.ai/v1/systemone');
  const body = JSON.parse(options.body);
  calls.push(body);
  // A real Response: the retained-receipt wrapper clones provider responses to read their structured answers.
  return new Response(JSON.stringify({ model: 'offline-wiring-only', answers:
    Object.fromEntries(Object.entries(body.questions).map(([key, question]) => {
      assert.equal(question.type, 'noul');
      return [key, { noul: queue ? queue.shift() : verdict }];
    })) }), { status: 200, headers: { 'content-type': 'application/json' } });
};
async function run(args) {
  const output = [], errors = [];
  const code = await main(args, { env: { PERCH_API_KEY: 'offline-wiring-only' },
    stdout: text => output.push(text), stderr: text => errors.push(text) });
  return { code, output: output.join('\n'), errors: errors.join('\n') };
}
try {
  // The rules file: seven advisory file rules, each reading only its own packet directory.
  const rules = YAML.parse(await readFile(join(root, '.perch/rules/prechecks.yaml'), 'utf8'));
  assert.deepEqual(rules.map(rule => rule.name), names);
  for (const rule of rules) {
    assert.equal(rule.each, 'file', rule.name);
    assert.equal(rule.gate, false, `${rule.name} must stay advisory until calibrated`);
    assert.equal(rule.min, FLOORS[rule.name], `${rule.name}: its floor is pinned here; a calibrated floor edits this map with its evidence`);
    assert.equal(rule.where, `.local/prechecks/packets/**/${rule.name}/*.md`, rule.name);
    assert.match(rule.ensure, /missing\s+evidence(?:,|\s+is)?\s+not a pass/i, `${rule.name} must say that missing evidence is not a pass`);
  }

  // A checkout that ignores `.local/**`, as the real perch.yaml does, with only this rules file installed.
  await mkdir(join(dir, '.perch/rules'), { recursive: true });
  await cp(join(root, '.perch/rules/prechecks.yaml'), join(dir, '.perch/rules/prechecks.yaml'));
  await cp(join(root, 'perch.yaml'), join(dir, 'perch.yaml'));
  const cases = JSON.parse(await readFile(join(root, 'tests/prechecks/perch-controls/cases.json'), 'utf8'));
  const staged = [];
  for (const [index, item] of cases.cases.entries()) {
    const text = await readFile(join(root, 'tests/prechecks/perch-controls', item.packet), 'utf8');
    const path = `.local/prechecks/packets/${item.increment}/${item.head.slice(0, 8)}/${item.rule}/${String(index + 1).padStart(4, '0')}.md`;
    await mkdir(dirname(join(dir, path)), { recursive: true });
    await writeFile(join(dir, path), text);
    staged.push({ ...item, path });
  }
  await mkdir(join(dir, 'docs'), { recursive: true });
  await writeFile(join(dir, 'docs/unrelated.md'), '# Unrelated\nNo packet, no claim.\n');
  await mkdir(join(dir, '.local/prechecks/packets/x/y/not-a-rule'), { recursive: true });
  await writeFile(join(dir, '.local/prechecks/packets/x/y/not-a-rule/0001.md'), '# Claim\nA packet in a directory no rule reads.\n');
  await writeFile(join(dir, '.gitignore'), '.local/\n');          // ignored and untracked packets are still read by an explicit check
  process.chdir(dir);
  execFileSync('git', ['init', '-q', '-b', 'main']);
  execFileSync('git', ['add', '.']);
  execFileSync('git', ['-c', 'user.name=Prechecks rule fixture', '-c', 'user.email=fixture@example.invalid',
    '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Offline rule wiring fixture']);

  const listed = await run(['rules', 'list', '--json']);
  assert.equal(listed.code, 0, listed.errors);
  const mine = JSON.parse(listed.output).filter(rule => rule.from !== 'perch');
  assert.deepEqual(mine.map(rule => rule.name).sort(), [...names].sort());
  assert.ok(mine.every(rule => rule.each === 'file' && !rule.disabled));

  // Each packet selects exactly its own rule, with one request of one question, even when every rule is named.
  for (const item of staged) {
    calls = []; verdict = 1;
    const result = await run(['check', item.path, '--rules', names.join(','), '--json']);
    assert.equal(result.code, 0, `${item.path}: ${result.errors}`);
    assert.equal(JSON.parse(result.output).checked, 1, `${item.path} selects exactly one rule`);
    assert.equal(calls.length, 1, item.path);
    const questions = Object.keys(calls[0].questions);
    assert.equal(questions.length, 1, item.path);
    assert.ok(questions[0].includes(item.rule) || JSON.stringify(calls[0].questions).includes(item.rule.split('-')[0]), item.path);
  }

  // An advisory verdict exits 3 with one finding; a passing one exits 0.
  const first = staged[0];
  calls = []; verdict = 0;
  const failing = await run(['check', first.path, '--rules', first.rule, '--json']);
  assert.equal(failing.code, 3, failing.errors);
  assert.equal(JSON.parse(failing.output).checked, 1);
  assert.equal(JSON.parse(failing.output).broken.length, 1);
  assert.equal(calls.length, 1);

  // An unrelated Markdown file, and a packet under a directory no rule reads, select nothing and cost no request.
  for (const target of ['docs/unrelated.md', '.local/prechecks/packets/x/y/not-a-rule/0001.md']) {
    calls = []; verdict = 1;
    const unrelated = await run(['check', target, '--rules', names.join(','), '--json']);
    assert.equal(unrelated.code, 0, unrelated.errors);
    assert.equal(JSON.parse(unrelated.output).checked, 0, target);
    assert.equal(calls.length, 0, target);
  }

  // The live runner, offline: a dry run makes no request; a live run through the retained-receipt wrapper makes one
  // request per packet, refuses a linked worktree, and reports whether the verdicts separate. The queued verdicts
  // below follow the labels, so this exercises the report logic only.
  const staging = '.local/prechecks/packets/controls';
  const { rows } = await plan({ root: dir, packets: staging, controls: true, controlsRoot: root });
  assert.equal(rows.length, cases.cases.length);
  assert.ok(rows.every(r => RULES_SET.has(r.rule) && r.expected && r.split));
  calls = []; verdict = 1;
  const dry = await execute(rows, { root: dir, live: false });
  assert.equal(dry.requests, 0);
  assert.equal(calls.length, 0);
  assert.ok(dry.results.every(r => r.status === 'planned'));
  await assert.rejects(execute(rows, { root: dir, env: {}, live: true, requireMain: false }), /No Perch credential/);
  queue = rows.map(r => (r.expected === 'broken' ? 0 : 1));
  const { runPerch } = await import('./perch-workflow.mjs');
  const live = await execute(rows, { root: dir, env: { PERCH_API_KEY: 'offline-wiring-only' }, live: true, requireMain: false, run: runPerch });
  assert.equal(calls.length, rows.length, 'one request per packet');
  assert.equal(live.results.length, rows.length);
  assert.ok(live.results.every(r => r.status === (r.expected === 'broken' ? 'flagged' : 'clean')));
  assert.equal(separation(live.results).separates, true);
  assert.ok(Object.values(separation(live.results).rules).every(rule => rule.separates), 'every rule separates on label-following verdicts');
  queue = null; verdict = 1;                   // a rule that never objects fails to flag any broken control
  const blind = await execute(rows, { root: dir, env: { PERCH_API_KEY: 'offline-wiring-only' }, live: true, requireMain: false, run: runPerch });
  const gap = separation(blind.results);
  assert.equal(gap.separates, false);
  assert.equal(gap.misclassified.length, cases.cases.filter(c => c.expected === 'broken').length);
  // Perch flags strictly above the rule's floor, so a verdict exactly at the floor is not a flag.
  assert.equal(flaggedAt({ probability_broken: 0.7, floor: 0.7 }), false);
  assert.equal(flaggedAt({ probability_broken: 0.71, floor: 0.7 }), true);
  const edge = separation([{ path: 'a', rule: 'r', expected: 'broken', probability_broken: 0.7, floor: 0.7 },
                           { path: 'b', rule: 'r', expected: 'clean', probability_broken: 0.7, floor: 0.7 }]);
  assert.deepEqual(edge.misclassified, ['a']);
  assert.equal(edge.rules.r.separates, false);
  // The dev split tunes a rule and the held-out split is asked once after its text is frozen: each plan asks only its own.
  for (const [split, allowed] of Object.entries(SPLITS)) {
    const chosen = (await plan({ root: dir, packets: staging, controls: true, controlsRoot: root, split })).rows;
    assert.equal(chosen.length, cases.cases.filter(c => allowed.includes(c.split)).length, split);
    assert.ok(chosen.every(r => allowed.includes(r.split)), split);
  }
  await assert.rejects(plan({ root: dir, packets: staging, controls: true, controlsRoot: root, split: 'test' }), /Unknown split/);
  await assert.rejects(plan({ root: dir, split: 'dev' }), /add --controls/);
  await assert.rejects(stageControls(dir, join(dir, 'docs')), /Refusing to stage/);
  await assert.rejects(stageControls(dir, resolve(dir, '..')), /Refusing to stage/);
  await assert.rejects(unstageControls(dir, join(dir, 'docs')), /Refusing to stage/);

  // The controls live beside the production packets while a calibration runs, and a production plan never asks them: it
  // skips the staged controls, and the calibration run removes them when it is done.
  const production = join(dir, PACKET_ROOT);
  const header = (rule, increment, head) => `<!-- prechecks packet v1; rule=${rule}; increment=${increment}; head=${head}; base=b1b1b1b1b1b1; builder=scripts/prechecks/packets@test; sources: none -->\n# Claim\nx\n\n# Evidence\ny\n\n# Scope\nz\n`;
  const put = async (relative, text) => { await mkdir(dirname(join(dir, relative)), { recursive: true }); await writeFile(join(dir, relative), text); };
  const beforeControls = (await plan({ root: dir })).rows.length;
  const withControls = await plan({ root: dir });
  assert.equal(withControls.rows.length, beforeControls);
  assert.ok(withControls.rows.every(r => !r.path.includes('/controls/')), 'production plans skip the staged controls');
  await unstageControls(dir, join(dir, staging));
  assert.equal((await plan({ root: dir })).rows.length, beforeControls);
  assert.ok(!(await readdir(production)).includes('controls'), 'the staged controls are removed');

  // The cap is per rule and per (increment, head) as each packet's header names them, not per directory depth: a default
  // run over one build asks every rule, the builder's limit and the runner's cap are one number, and skips are counted.
  assert.equal(CAP, JSON.parse(await readFile(join(root, 'scripts/prechecks/packets/limits.json'), 'utf8')).packets_per_rule_per_head);
  const fresh = '.local/prechecks/cap-fixture';
  await rm(join(dir, fresh), { recursive: true, force: true });
  for (const rule of names) {
    for (const [head, count] of [['d2fe0f20aaaa', 3], ['454bf305bbbb', 3]]) {
      for (let n = 1; n <= count; n++) await put(`${fresh}/vm-spec/${head.slice(0, 8)}/${rule}/${String(n).padStart(4, '0')}.md`, header(rule, 'vm-spec', head));
    }
  }
  const capped = await plan({ root: dir, packets: fresh, cap: 2 });
  assert.equal(capped.rows.length, names.length * 2 * 2, 'two per rule and head, and every rule is asked');
  assert.deepEqual(Object.fromEntries(names.map(name => [name, 2])), capped.skipped, 'the skipped packets are counted by rule');
  assert.ok(names.every(name => capped.rows.filter(r => r.rule === name).length === 4));
  assert.equal((await plan({ root: dir, packets: fresh })).rows.length, names.length * 6, 'the default cap asks the whole build');
  const deep = await plan({ root: dir, packets: `${fresh}/vm-spec/d2fe0f20`, cap: 2 });   // a deeper --packets directory: the same groups
  assert.equal(deep.rows.length, names.length * 2);
  assert.deepEqual(await readHeader(join(dir, fresh, 'vm-spec/d2fe0f20', names[0], '0001.md')), { rule: names[0], increment: 'vm-spec', head: 'd2fe0f20aaaa' });
  assert.equal(await readHeader(join(dir, 'docs/unrelated.md')), null);

  // A packet directory built anywhere else is staged into the rules' glob before it is asked, and a dry run only says so.
  const elsewhere = '.local/packets-vm-spec';
  await rm(join(dir, elsewhere), { recursive: true, force: true });
  await put(`${elsewhere}/vm-spec/d2fe0f20/claim-holds-against-evidence/0001.md`, header('claim-holds-against-evidence', 'vm-spec', 'd2fe0f20aaaa'));
  await put(`${elsewhere}/vm-spec/d2fe0f20/passages-agree/0001.md`, header('passages-agree', 'vm-spec', 'd2fe0f20aaaa'));
  const outside = await plan({ root: dir, packets: elsewhere });
  assert.equal(outside.staged, 2);
  assert.ok(outside.rows.every(r => r.source && inWhere(r.path, r.rule) && r.path.startsWith(`${PACKET_ROOT}/staged/vm-spec/d2fe0f20aaaa/`)), outside.rows);
  assert.ok(!inWhere('.local/packets-vm-spec/x/passages-agree/0001.md', 'passages-agree'));
  assert.ok(inWhere(`${PACKET_ROOT}/a/b/passages-agree/0001.md`, 'passages-agree'));
  assert.ok(!inWhere(`${PACKET_ROOT}/a/b/passages-agree/0001.md`, 'clause-vs-delta'));
  assert.ok(!inWhere(`${PACKET_ROOT}/../x/passages-agree/0001.md`, 'passages-agree'));
  calls = []; verdict = 1;
  await execute(outside.rows, { root: dir, live: false });
  assert.ok(!existsSync(join(dir, outside.rows[0].path)), 'a dry run copies nothing');
  const asked = await execute(outside.rows, { root: dir, env: { PERCH_API_KEY: 'offline-wiring-only' }, live: true, requireMain: false, run: runPerch });
  assert.equal(calls.length, 2, 'each staged packet is asked once, from a path the rules select');
  assert.ok(asked.results.every(r => r.checked === 1 && r.status === 'clean'), asked.results);
  assert.ok(existsSync(join(dir, outside.rows[0].path)));
  assert.equal((await plan({ root: dir })).rows.filter(r => r.path.includes('/staged/')).length, 0, 'a production plan does not ask the staged copies again');
  await assert.rejects(execute([{ path: 'docs/unrelated.md', rule: 'passages-agree' }],
    { root: dir, env: { PERCH_API_KEY: 'offline-wiring-only' }, live: true, requireMain: false, run: runPerch }), /Refusing docs\/unrelated\.md/);

  // The calibration set: every rule has DEV_MIN dev controls of each label, every held-out cell is present or a documented gap,
  // dev labels follow the split, and every packet is self-contained, bounded and free of host paths.
  const gaps = new Set(cases.gaps.map(g => `${g.rule}/${g.split === 'held-out' ? `held-out/${g.expected}` : g.split}`));
  for (const gap of cases.gaps) assert.ok(gap.reason.length > 40, `gap ${gap.rule}/${gap.split} needs a reason`);
  for (const name of names) {
    for (const cell of cells) {
      const found = cases.cases.filter(c => c.rule === name && cellOf(c) === cell);
      if (!cell.startsWith('held-out')) {
        assert.ok(found.length >= DEV_MIN, `${name}/${cell}: ${found.length} dev controls, at least ${DEV_MIN} required`);
        assert.ok(!gaps.has(`${name}/${cell}`), `${name}/${cell}: a dev cell is never a gap`);
        continue;
      }
      assert.ok(found.length > 0 || gaps.has(`${name}/${cell}`), `${name}/${cell}: neither a control nor a documented gap`);
      assert.ok(found.length === 0 || !gaps.has(`${name}/${cell}`), `${name}/${cell}: a control exists, so it is no gap`);
    }
  }
  assert.equal(new Set(cases.cases.map(c => `${c.split}-${c.id}`)).size, cases.cases.length, 'control ids are unique');
  for (const item of cases.cases) {
    assert.ok(['broken', 'clean', 'held-out'].includes(item.split), item.id);
    assert.ok(item.split === 'held-out' ? ['broken', 'clean'].includes(item.expected) : item.expected === item.split, item.id);
    const text = await readFile(join(root, 'tests/prechecks/perch-controls', item.packet), 'utf8');
    assert.ok(text.length > 200 && text.length <= 48 * 1024, `${item.id}: packet size`);
    assert.match(text, /^<!-- prechecks packet v1; rule=[a-z0-9-]+; increment=/, item.id);
    for (const heading of ['# Claim', '# Evidence', '# Scope']) assert.ok(text.includes(`\n${heading}\n`), `${item.id}: ${heading}`);
    assert.ok(!/\/Users\/|\/private\/|\/home\/[a-z]/.test(text), `${item.id}: host path in a packet`);
  }
  console.log(`PASS: seven advisory prechecks rules; ${cases.cases.length} calibration packets each select exactly their own rule; one request per packet; advisory finding exit 3; unrelated and unmatched packets select nothing; every rule has ${DEV_MIN} dev controls of each label and a held-out control or a documented gap of each.`);
  console.log('No provider contacted. This verifies wiring, not model accuracy or that any rule separates broken from clean.');
} finally {
  globalThis.fetch = realFetch;
  process.chdir(previous);
  await rm(dir, { recursive: true, force: true });
}
