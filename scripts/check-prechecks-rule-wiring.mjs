#!/usr/bin/env node
// Offline CLI integration check for .perch/rules/prechecks.yaml. Stub probabilities are never calibration data:
// this proves selection and plumbing, not that any rule separates broken packets from clean ones.
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import YAML from '../node_modules/yaml/dist/index.js';
import { main } from '../node_modules/@lakeday/perch/dist/cli.mjs';
import { execute, plan, separation, stageControls } from './prechecks-perch-run.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const names = [
  'claim-holds-against-evidence', 'passages-agree', 'outcome-follows-d4', 'clause-vs-delta',
  'expectation-independent', 'kill-is-semantic', 'required-laws-met',
];
const splits = ['broken', 'clean', 'held-out'];
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
    assert.equal(rule.min, 80, rule.name);
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
  const rows = await plan({ root: dir, packets: staging, controls: true, controlsRoot: root });
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
  queue = null; verdict = 1;                   // a rule that never objects fails to flag any broken control
  const blind = await execute(rows, { root: dir, env: { PERCH_API_KEY: 'offline-wiring-only' }, live: true, requireMain: false, run: runPerch });
  const gap = separation(blind.results);
  assert.equal(gap.separates, false);
  assert.equal(gap.misclassified.length, cases.cases.filter(c => c.expected === 'broken').length);
  await assert.rejects(stageControls(dir, join(dir, 'docs')), /Refusing to stage/);
  await assert.rejects(stageControls(dir, resolve(dir, '..')), /Refusing to stage/);

  // The calibration set: every rule has a broken control, every rule and split is present or a documented gap,
  // labels follow the split, and every packet is self-contained, bounded and free of host paths.
  assert.ok(cases.cases.length >= names.length * 2, 'controls present');
  const gaps = new Set(cases.gaps.map(g => `${g.rule}/${g.split}`));
  for (const gap of cases.gaps) assert.ok(gap.reason.length > 40, `gap ${gap.rule}/${gap.split} needs a reason`);
  for (const name of names) {
    for (const split of splits) {
      const found = cases.cases.filter(c => c.rule === name && c.split === split);
      assert.ok(found.length > 0 || gaps.has(`${name}/${split}`), `${name}/${split}: neither a control nor a documented gap`);
      assert.ok(found.length === 0 || !gaps.has(`${name}/${split}`), `${name}/${split}: a control exists, so it is no gap`);
    }
    assert.ok(cases.cases.some(c => c.rule === name && c.split === 'broken'), `${name} needs a broken control`);
  }
  for (const item of cases.cases) {
    assert.equal(item.expected, item.split === 'clean' ? 'clean' : 'broken', item.id);
    const text = await readFile(join(root, 'tests/prechecks/perch-controls', item.packet), 'utf8');
    assert.ok(text.length > 200 && text.length <= 48 * 1024, `${item.id}: packet size`);
    assert.match(text, /^<!-- prechecks packet v1; rule=[a-z0-9-]+; increment=/, item.id);
    for (const heading of ['# Claim', '# Evidence', '# Scope']) assert.ok(text.includes(`\n${heading}\n`), `${item.id}: ${heading}`);
    assert.ok(!/\/Users\/|\/private\/|\/home\/[a-z]/.test(text), `${item.id}: host path in a packet`);
  }
  console.log(`PASS: seven advisory prechecks rules; ${cases.cases.length} calibration packets each select exactly their own rule; one request per packet; advisory finding exit 3; unrelated and unmatched packets select nothing; every rule and split has a control or a documented gap.`);
  console.log('No provider contacted. This verifies wiring, not model accuracy or that any rule separates broken from clean.');
} finally {
  globalThis.fetch = realFetch;
  process.chdir(previous);
  await rm(dir, { recursive: true, force: true });
}
