import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as style from '../scripts/perch-style.mjs';

// Version 6: the shared pattern sheet, figure manifests, declared leads, advisory proof fills and inventory scopes.
const live = JSON.parse(await readFile(new URL('../perch-style.json', import.meta.url), 'utf8'));
assert.equal(live.version, 6);
const config = structuredClone(live);
config.pattern_sheet.path = 'SHEET.md';
const sheetText = '# Shapes\n\nS1 Fuel-first machine: match fuel state; stop arms first; one advancing arm.\n';
const scaled = ['highly_memetic', 'anticipation', 'payoff'];
const unit = 'import Base\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: helper(x)\ndef unrelated() -> U32: 7\n';
const laws = 'import Base\nimport ./unit.bend as U\nlaw solve_one:\n  for +x: U32\n  {U.solve(x) == U32.add(x,1) : U32}\n';
const proofs = 'import Base\nimport ./unit.bend as U\nimport ./LAWS.bend as L\ndef L.solve_one(x): {==}\n';
const manifest = { schema: 1, id: 'successor', title: 'Successor figure', shapes: ['S1'],
  declarations: ['unit.bend::helper', 'unit.bend::solve', 'LAWS.bend::solve_one', 'PROOF.bend::L.solve_one'],
  leads: ['unit.bend::solve'], interfaces: [] };
const score = (value, count) => ({ type: 'score', score: value, confidence: 1,
  probabilities: Object.fromEntries(Array.from({ length: count }, (_, i) => [i, i === value ? 1 : 0])) });
const binary = probability => ({ type: 'score', score: probability, confidence: 0.8, probabilities: { 0: 1 - probability, 1: probability } });

async function fixture(t, { sheet = sheetText, figure = manifest } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'perch-style-figure-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(config));
  if (sheet !== null) await writeFile(join(root, 'SHEET.md'), sheet);
  await writeFile(join(root, 'unit.bend'), unit);
  await writeFile(join(root, 'LAWS.bend'), laws);
  await writeFile(join(root, 'PROOF.bend'), proofs);
  if (figure) await writeFile(join(root, 'figure.json'), JSON.stringify(figure));
  return root;
}

/** Answers every question; `grade(name, id)` may override a declaration's level. */
function provider({ role = 0, family = 3, grade = () => null } = {}) {
  const requests = [];
  return { requests, fetchImpl: async (_url, options) => {
    const request = JSON.parse(options.body);
    requests.push(request);
    const composition = Array.isArray(request.state.files);
    const answers = Object.fromEntries(Object.entries(request.questions).map(([id, question]) => [id,
      id === 'style_role' ? binary(role) : id === 'criticality' ? binary(1)
        : id === 'potential_profundity' ? score(0, question.criteria.length)
          : score(composition ? family : grade(request.state.name, id) ?? (scaled.includes(id) && role < 0.6 ? 2 : 3), question.criteria.length)]));
    return { ok: true, json: async () => ({ model: 'jev-1.13.0', answers, usage: { input_tokens: 10, output_tokens: 2 } }) };
  } };
}

async function run(root, p, options = [], targets = []) {
  const output = [];
  const code = await style.runStyleRanking(['--live', '--json', ...options, ...targets], { root,
    env: { PERCH_API_KEY: 'mock-only', PERCH_MODEL_ID: 'jev-1.13.0' }, fetchImpl: p.fetchImpl,
    stdout: text => output.push(text), stderr: () => {} });
  return { code, report: JSON.parse(output[0]) };
}

test('the pattern sheet reaches every declaration and composition request and is part of each identity', async t => {
  const root = await fixture(t), p = provider();
  const { report, code } = await run(root, p, [], ['unit.bend::solve']);
  assert.equal(code, 0, 'a supporting declaration whose whole-file composition meets the leading bar qualifies');
  const declaration = p.requests.filter(r => !Array.isArray(r.state.files));
  assert.equal(declaration.length, 1);
  assert.equal(declaration[0].state.sheet, sheetText);
  const composition = p.requests.find(r => Array.isArray(r.state.files));
  assert.equal(composition.state.sheet, sheetText);
  assert.equal(report.pattern_sheet.path, 'SHEET.md');
  assert.equal(report.pattern_sheet.bytes, Buffer.byteLength(sheetText));
  assert.equal(report.rows[0].sheet_sha256, report.pattern_sheet.sha256);
  assert.ok(!('sheet' in report.rows[0]), 'receipts keep the sheet by hash, not by copy, in declaration rows');
  const before = report.rows[0].state_sha256;
  await writeFile(join(root, 'SHEET.md'), `${sheetText}\nS9 Another shape.\n`);
  const changed = await run(root, provider(), [], ['unit.bend::solve']);
  assert.notEqual(changed.report.rows[0].state_sha256, before, 'sheet text is part of the request identity');
});

test('a missing or oversized sheet fails before any paid request; an unconfigured sheet keeps the v5 request shape', async t => {
  const root = await fixture(t, { sheet: null }), p = provider();
  await assert.rejects(run(root, p, [], ['unit.bend::solve']), /Pattern sheet required/);
  assert.equal(p.requests.length, 0);
  await writeFile(join(root, 'SHEET.md'), 'x'.repeat(config.pattern_sheet.max_bytes + 1));
  await assert.rejects(run(root, p, [], ['unit.bend::solve']), /at most/);
  assert.equal(p.requests.length, 0);
  const plain = structuredClone(config);
  delete plain.pattern_sheet;
  await writeFile(join(root, 'perch-style.json'), JSON.stringify(plain));
  const { code } = await run(root, p, [], ['unit.bend::solve']);
  assert.equal(code, 0);
  assert.ok(p.requests.every(r => !('sheet' in r.state)));
  assert.throws(() => style.assessStyle([], { ...config, pattern_sheet: { path: 'sheet.txt', max_bytes: 100 } }), /Markdown path/);
});

test('a figure manifest selects declarations across files, forces declared leads to level 3 and keeps model roles for members', async t => {
  const root = await fixture(t), p = provider({ role: 0 });
  const { report, code } = await run(root, p, ['--figure=figure.json']);
  assert.equal(code, 3, 'the declared lead fails its level-3 bar on a level-2 answer');
  assert.equal(report.mode, 'figure');
  assert.equal(report.figure.id, 'successor');
  assert.deepEqual(report.figure.leads, ['unit.bend::solve']);
  assert.deepEqual(report.figure.shapes_claimed, ['S1']);
  assert.deepEqual(report.rows.map(r => r.target), manifest.declarations);
  assert.deepEqual(report.rows.map(r => r.figure.role), ['member', 'lead', 'member', 'member']);
  const solve = report.assessments.filter(a => a.target === 'unit.bend::solve' && scaled.includes(a.dimension));
  assert.ok(solve.every(a => a.target_level === 3 && a.style_role === 'leading' && a.role_basis === 'manifest_lead'));
  assert.ok(solve.every(a => a.status === 'below_target'), 'a level-2 answer cannot satisfy a declared lead');
  const helper = report.assessments.filter(a => a.target === 'unit.bend::helper' && scaled.includes(a.dimension));
  assert.ok(helper.every(a => a.target_level === 2 && a.style_role === 'supporting' && a.role_basis === 'model' && a.status === 'meets_target'));
  const lead = report.style_role.assessments.find(a => a.target === 'unit.bend::solve');
  assert.equal(lead.status, 'leading');
  assert.equal(lead.model_status, 'supporting', 'the model classification stays recorded beside the manifest lead');
  assert.equal(report.style_summary.meets_all, 3);
  assert.equal(report.status, 'completed', 'declaration attention does not become failure when the run itself completed');
});

test('the figure composition sees exactly the manifest declarations, its interfaces and the sheet, never whole files', async t => {
  const root = await fixture(t), p = provider({ role: 1 });
  const { report, code } = await run(root, p, ['--figure=figure.json']);
  assert.equal(code, 0);
  const composition = p.requests.find(r => Array.isArray(r.state.files));
  assert.deepEqual(composition.state.figure, { id: 'successor', title: 'Successor figure' });
  assert.ok(!('shapes' in composition.state) && !('reading_hypothesis' in composition.state), 'author claims are not request context');
  assert.deepEqual(composition.state.files.map(f => f.path), ['unit.bend', 'LAWS.bend', 'PROOF.bend']);
  assert.deepEqual(composition.state.files[0].declarations.map(d => d.name), ['helper', 'solve']);
  assert.ok(!JSON.stringify(composition.state.files).includes('unrelated'), 'unselected declarations stay out of the figure');
  assert.equal(composition.state.sheet, sheetText);
  assert.deepEqual(composition.state.interfaces, []);
  assert.equal(report.composition.available, true);
  assert.equal(report.composition.context.basis, 'figure-manifest');
  assert.equal(report.composition.context.declarations, 4);
  assert.equal(report.composition.assessment.status, 'meets_target');
  assert.equal(report.qualification.fully_qualified, true);
});

test('proof fills inside a figure are advisory and visible; outside a figure the same fill still gates', async t => {
  const root = await fixture(t);
  const low = (name, id) => name === 'L.solve_one' && id === 'highly_memetic' ? 0 : null;
  const inFigure = await run(root, provider({ role: 1, grade: low }), ['--figure=figure.json']);
  assert.equal(inFigure.code, 0);
  const fill = inFigure.report.assessments.filter(a => a.target === 'PROOF.bend::L.solve_one');
  assert.ok(fill.length >= 3 && fill.every(a => a.advisory === true && a.figure === 'successor'));
  assert.equal(fill.find(a => a.dimension === 'highly_memetic').status, 'below_target');
  assert.equal(inFigure.report.style_summary.advisory.assessments, fill.length);
  assert.equal(inFigure.report.style_summary.advisory.below_target, 1);
  assert.equal(inFigure.report.style_summary.meets_all, 4);
  assert.ok(inFigure.report.assessments.filter(a => a.target !== 'PROOF.bend::L.solve_one').every(a => a.advisory === false));
  const alone = await run(root, provider({ role: 1, grade: low }), [], ['PROOF.bend::L.solve_one']);
  assert.equal(alone.code, 3);
  assert.ok(alone.report.assessments.every(a => !('advisory' in a)));
  assert.equal(alone.report.style_summary.below_target, 1);
  assert.equal(alone.report.style_summary.advisory.assessments, 0);
});

test('opaque interfaces resolve collaborators outside the figure; without them the composition stays unavailable', async t => {
  const root = await fixture(t);
  await writeFile(join(root, 'unit.bend'), 'import Base\nimport ./ext.bend as X\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: X.next(helper(x))\n');
  await writeFile(join(root, 'ext.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,2)\n');
  const bare = await run(root, provider({ role: 1 }), ['--figure=figure.json']);
  assert.equal(bare.code, 3);
  assert.equal(bare.report.composition.available, false);
  assert.deepEqual(bare.report.composition.reasons, ['unresolved_composition_context']);
  assert.deepEqual(bare.report.composition.context.unresolved, [{ path: 'unit.bend', name: 'X.next', reason: 'collaborator-not-in-figure' }]);
  await writeFile(join(root, 'figure.json'), JSON.stringify({ ...manifest,
    interfaces: [{ name: 'X.next', signature: 'def next(x: U32) -> U32', note: 'Opaque successor stage.' }] }));
  const p = provider({ role: 1 }), stubbed = await run(root, p, ['--figure=figure.json']);
  assert.equal(stubbed.code, 0);
  assert.equal(stubbed.report.composition.available, true);
  const composition = p.requests.find(r => Array.isArray(r.state.files));
  assert.deepEqual(composition.state.interfaces, [{ name: 'X.next', signature: 'def next(x: U32) -> U32', note: 'Opaque successor stage.' }]);
  assert.deepEqual(stubbed.report.figure.interfaces, ['X.next']);
});

test('manifest validation rejects malformed figures before requests; a manifest task is the default fixed task', async t => {
  const root = await fixture(t), p = provider();
  for (const broken of [
    { ...manifest, leads: [] },
    { ...manifest, leads: ['unit.bend::missing'] },
    { ...manifest, declarations: [...manifest.declarations, 'unit.bend::solve'] },
    { ...manifest, declarations: ['unit.bend'] },
    { ...manifest, interfaces: [{ name: 'X.next' }] },
    { ...manifest, schema: 2 },
    { ...manifest, id: 'Bad Id' },
  ]) {
    await writeFile(join(root, 'figure.json'), JSON.stringify(broken));
    await assert.rejects(run(root, p, ['--figure=figure.json']), /Invalid figure manifest/);
  }
  await writeFile(join(root, 'figure.json'), JSON.stringify({ ...manifest, declarations: [...manifest.declarations, 'unit.bend::absent'] }));
  await assert.rejects(run(root, p, ['--figure=figure.json']), /No applicable parsed declaration/);
  await assert.rejects(run(root, p, ['--figure=figure.json'], ['unit.bend']), /alone/);
  await assert.rejects(run(root, p, ['--figure=figure.json', '--all']), /alone/);
  assert.equal(p.requests.length, 0);
  await writeFile(join(root, 'contract.md'), 'Return the successor of an unsigned word.');
  await writeFile(join(root, 'figure.json'), JSON.stringify({ ...manifest, task: 'contract.md' }));
  const { report, code } = await run(root, provider({ role: 1 }), ['--figure=figure.json']);
  assert.equal(code, 0);
  assert.equal(report.potential_profundity.task.origin, 'task-file');
  assert.equal(report.potential_profundity.task.path, 'contract.md');
  assert.equal(report.figure.task, 'contract.md');
});

test('a changed sheet or manifest during review is disclosed as stale source', async t => {
  const root = await fixture(t);
  const p = provider({ role: 1 });
  let touched = false;
  const fetchImpl = async (url, options) => {
    if (!touched) { touched = true; await writeFile(join(root, 'SHEET.md'), `${sheetText}\nS9 Late edit.\n`); }
    return p.fetchImpl(url, options);
  };
  const output = [];
  const code = await style.runStyleRanking(['--live', '--json', '--figure=figure.json'], { root,
    env: { PERCH_API_KEY: 'mock-only', PERCH_MODEL_ID: 'jev-1.13.0' }, fetchImpl, stdout: text => output.push(text), stderr: () => {} });
  const report = JSON.parse(output[0]);
  assert.equal(code, 3);
  assert.deepEqual(report.source_freshness.changed_sources, ['SHEET.md']);
  assert.equal(report.qualification.fully_qualified, false);
});

test('project inventory partitions fixtures and evidence from gated mechanisms without changing any rating', async t => {
  const root = await fixture(t);
  await mkdir(join(root, 'src'), { recursive: true });
  await mkdir(join(root, 'tests'), { recursive: true });
  await writeFile(join(root, 'src/a.bend'), 'import Base\ndef a(x: U32) -> U32: U32.add(x,1)\n');
  await writeFile(join(root, 'tests/fixture.bend'), 'import Base\ndef probe(x: U32) -> U32: U32.add(x,9)\n');
  execFileSync('git', ['init', '--quiet'], { cwd: root });
  const { report, code } = await run(root, provider({ role: 1, grade: (name, id) => name === 'probe' && id === 'highly_memetic' ? 0 : null }), ['--all']);
  assert.equal(code, 3);
  assert.equal(report.mode, 'project');
  const scopes = Object.fromEntries(report.style_summary.by_scope.map(scope => [scope.id, scope]));
  assert.equal(scopes.fixture.gate, false);
  assert.equal(scopes.fixture.declarations, 1);
  assert.equal(scopes.fixture.needs_review, 1);
  assert.equal(scopes.mechanism.gate, true);
  assert.ok(scopes.mechanism.declarations >= 4);
  assert.equal(scopes.mechanism.needs_review, 0);
  assert.equal(scopes.evidence.declarations, 0);
  assert.equal(style.inventoryScope('packages/vec/campaigns/x/candidate.bend', config).id, 'evidence');
  assert.equal(style.inventoryScope('packages/vec/main.bend', config).id, 'mechanism');
  assert.equal(style.inventoryScope('tests/subsets/x.bend', config).id, 'fixture');
  assert.throws(() => style.assessStyle([], { ...config, inventory_scopes: [{ id: 'only', gate: false, patterns: [] }] }), /gated default/);
});

test('inside a figure each member sees the figure as its context: no cap-based truncation, laws and interfaces attached, gaps recorded per member', async t => {
  const root = await fixture(t);
  await writeFile(join(root, 'unit.bend'), 'import Base\nimport ./ext.bend as X\ndef helper(x: U32) -> U32: U32.add(x,1)\ndef solve(x: U32) -> U32: X.next(helper(x))\ndef unrelated() -> U32: 7\n');
  await writeFile(join(root, 'ext.bend'), 'import Base\ndef next(x: U32) -> U32: U32.add(x,2)\n');
  await writeFile(join(root, 'figure.json'), JSON.stringify({ ...manifest,
    interfaces: [{ name: 'X.next', signature: 'def next(x: U32) -> U32' }] }));
  const p = provider({ role: 1 }), { report, code } = await run(root, p, ['--figure=figure.json']);
  assert.equal(code, 0);
  const requests = Object.fromEntries(p.requests.filter(r => !Array.isArray(r.state.files)).map(r => [r.state.name, r.state]));
  assert.deepEqual(requests.solve.calls.map(c => c.name), ['helper']);
  assert.deepEqual(requests.helper.called_by.map(c => c.name), ['solve']);
  assert.deepEqual(requests.solve.laws.map(l => l.name), ['solve_one'], 'a law that names the declaration travels with it');
  assert.deepEqual(requests.solve.interfaces, [{ name: 'X.next', signature: 'def next(x: U32) -> U32' }]);
  const supplied = JSON.stringify([requests.solve.source, requests.solve.calls, requests.solve.called_by, requests.solve.laws, requests.solve.datatypes]);
  assert.ok(!supplied.includes('def unrelated'), 'unselected same-file declarations stay outside the figure');
  assert.equal(requests.solve.context_notes.basis, 'figure-manifest');
  assert.ok(report.rows.every(row => row.context.truncated === false && row.context.basis === 'figure-manifest'));
  assert.ok(report.diagnostics.assessments.every(a => a.status === 'rated'), 'figure context never fabricates unavailable diagnostics for capped helpers');
  await writeFile(join(root, 'figure.json'), JSON.stringify(manifest));
  const gap = await run(root, provider({ role: 1 }), ['--figure=figure.json']);
  const solve = gap.report.rows.find(r => r.target === 'unit.bend::solve');
  assert.deepEqual(solve.context.unresolved, [{ path: 'unit.bend', name: 'X.next', reason: 'collaborator-not-in-figure' }]);
  assert.equal(gap.report.style_role.assessments.find(a => a.target === 'unit.bend::solve').context_limited, true);
  assert.equal(gap.report.rows.find(r => r.target === 'unit.bend::helper').context.unresolved.length, 0);
});
