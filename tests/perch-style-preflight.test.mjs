import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runStyleRanking } from '../scripts/perch-style.mjs';

// The current production rubric: preflight must describe the requests a live run would send.
const config = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
const forbidden = async () => { throw new Error('preflight must not contact a provider'); };

async function fixture(t, files) {
  const root = await mkdtemp(join(tmpdir(), 'perch-style-preflight-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  for (const [path, source] of Object.entries(files)) await writeFile(join(root, path), source);
  return root;
}

async function preflight(root, args) {
  const output = [];
  const code = await runStyleRanking(['--preflight', '--json', ...args], { root,
    env: { PERCH_API_KEY: 'offline-secret-must-not-be-used' }, fetchImpl: forbidden, stdout: x => output.push(x) });
  return { code, report: JSON.parse(output.join('\n')) };
}

const direct = 'import Base\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: helper(x)\n';
// Five same-file callers exceed the four-caller context bound.
const popular = ['import Base', 'def core(x: U32) -> U32: U32.add(x,1)',
  ...[1, 2, 3, 4, 5].map(n => `def use${n}(x: U32) -> U32: core(x)`)].join('\n') + '\n';

test('complete context and composition are structurally unblocked, with no provider or receipt', async t => {
  const root = await fixture(t, { 'unit.bend': direct });
  const { code, report } = await preflight(root, ['--cohort=Add one to a word', 'unit.bend']);
  assert.equal(code, 0);
  assert.equal(report.command, 'style-preflight');
  assert.equal(report.provider_requests, 0);
  assert.equal(report.summary.truncated_units, 0);
  assert.equal(report.summary.supporting_role_impossible, 0);
  assert.equal(report.composition.available, true);
  assert.deepEqual(report.units.map(u => [u.target, u.diagnostics_available, u.supporting_role_possible]),
    [['unit.bend::helper', true, true], ['unit.bend::solve', true, true]]);
  await assert.rejects(stat(join(root, '.perch')), { code: 'ENOENT' });
});

test('a truncated caller context is reported as unpassable and forbids the supporting role', async t => {
  const root = await fixture(t, { 'popular.bend': popular });
  const { code, report } = await preflight(root, ['popular.bend::core']);
  assert.equal(code, 3);
  const [unit] = report.units;
  assert.equal(unit.truncated, true);
  assert.equal(unit.diagnostics_available, false);
  assert.equal(unit.supporting_role_possible, false);
  assert.deepEqual(report.summary.truncated_by_limit, { 'caller-or-byte-limit': 1 });
  assert.equal(report.structural_blockers, 1);
});

test('an unresolvable collaborator makes composition unavailable and names the reason', async t => {
  const root = await fixture(t, {
    'remote.bend': 'import Base\nimport pkg@1.2.3.4/lib.bend as P\ndef solve(x: U32) -> U32: P.next(x)\n' });
  const { code, report } = await preflight(root, ['remote.bend']);
  assert.equal(code, 3);
  assert.equal(report.composition.available, false);
  assert.deepEqual(report.composition.reasons, ['unresolved_composition_context']);
  assert.deepEqual(report.composition.unresolved_by_reason, { 'nonlocal-import': 1 });
  assert.equal(report.units[0].supporting_role_possible, false);
});

test('project preflight lists unranked files and single-file groups without ratings', async t => {
  const root = await fixture(t, { 'unit.bend': direct, 'broken.bend': 'import Base\ndef bad( -> U32: 0\n' });
  execFileSync('git', ['init', '-q'], { cwd: root });
  const { code, report } = await preflight(root, ['--all']);
  assert.equal(code, 3);
  assert.equal(report.mode, 'project');
  assert.deepEqual(report.inventory.unranked.map(file => file.path), ['broken.bend']);
  assert.deepEqual(report.file_groups.map(group => [group.path, group.units, group.available]), [['unit.bend', 2, true]]);
  assert.equal(report.summary.single_file_groups_available, 1);
  assert.deepEqual(report.composition, { required: 'always', available: false, reasons: ['explicit_selected_group_required'] });
});

test('project preflight, like a live --all run, cannot qualify without an explicit composition group', async t => {
  const root = await fixture(t, { 'unit.bend': direct });
  execFileSync('git', ['init', '-q'], { cwd: root });
  const { code, report } = await preflight(root, ['--all']);
  assert.equal(code, 3);
  assert.equal(report.summary.truncated_units + report.summary.unranked_files, 0);
  assert.equal(report.structural_blockers, 1);
  assert.deepEqual(report.composition.reasons, ['explicit_selected_group_required']);
});

test('task handling and empty inventories match the live run', async t => {
  const root = await fixture(t, { 'unit.bend': direct, 'long.md': 'x'.repeat(config.potential_profundity.max_task_bytes + 1) });
  const empty = await preflight(root, ['--cohort=', 'unit.bend']);
  assert.equal(empty.code, 0);
  assert.deepEqual([empty.report.task.origin, empty.report.task.available, empty.report.task.reason], ['explicit-cohort', false, 'missing_task_context']);
  const long = await preflight(root, ['--task=long.md', 'unit.bend']);
  assert.deepEqual([long.report.task.available, long.report.task.reason], [false, 'task_byte_limit']);
  const bare = await fixture(t, { 'types.bend': 'import Base\n' });
  execFileSync('git', ['init', '-q'], { cwd: bare });
  await assert.rejects(runStyleRanking(['--preflight', '--all'], { root: bare, env: {}, fetchImpl: forbidden, stdout: () => {} }),
    /No rankable parsed declarations/);
});

test('preflight refuses live mode, unknown options and existing output', async t => {
  const root = await fixture(t, { 'unit.bend': direct, 'old.json': '{}' });
  const run = args => runStyleRanking(args, { root, env: {}, fetchImpl: forbidden, stdout: () => {} });
  await assert.rejects(run(['--preflight', '--live', 'unit.bend']), /not both/);
  await assert.rejects(run(['--preflight', '--jobs=2', 'unit.bend']), /never contacts a provider/);
  await assert.rejects(run(['--preflight']), /either --all or explicit targets/);
  await assert.rejects(run(['--preflight', '--output=old.json', 'unit.bend']), /already exists/);
});
