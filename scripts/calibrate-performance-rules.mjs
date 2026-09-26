#!/usr/bin/env node
// Explicit paid checks; result labels are never inferred from provider answers.
import { createHash } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPerch } from './perch-workflow.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const digest = data => createHash('sha256').update(data).digest('hex');
if (!process.argv.includes('--live')) {
  console.error('Use --live to authorize this paid calibration run.');
  process.exit(2);
}
const manifest = process.argv.find(x => x.startsWith('--manifest='))?.slice(11);
const mapping = {
  'growing-prefix-copy': 'perf-growing-prefix-copy',
  'invariant-summary': 'perf-loop-invariant-work',
  'indexed-linked-list': 'perf-linked-list-indexing',
};
const controls = manifest ? JSON.parse(await readFile(resolve(root, manifest), 'utf8')) : [
  ...Object.entries(mapping).flatMap(([id, rule]) => ['baseline', 'clean', 'held-out/broken', 'held-out/clean'].map(split => ({
    id: `${id}/${split}`, rule, split, expected: split.endsWith('clean') ? 'holds' : 'violates',
    path: `tests/perch-performance/cases/${id}/${split.startsWith('held-out/') ? split + '.bend' : split + '/main.bend'}`,
  }))),
  ...['baseline', 'clean', 'held-out'].map(split => ({
    id: `amortized-growth/${split}`, rule: 'perf-amortized-growth', split,
    expected: split === 'clean' ? 'holds' : 'violates',
    path: `tests/perch-performance-growth/${split}.mjs`,
    unit: split === 'held-out' ? 'encode' : 'Bytes.append',
  })),
];
const started = new Date().toISOString();
const output = process.argv.find(x => x.startsWith('--output='))?.slice(9)
  ?? `docs/perch-calibration/performance-${started.slice(0, 10)}.json`;
// Verify every input exists before spending any provider calls.
for (const control of controls) await readFile(resolve(root, control.path));
const rows = [];
for (const control of controls) {
  const source = await readFile(resolve(root, control.path));
  const target = control.unit ? `${control.path}::${control.unit}` : control.path;
  const exit = await runPerch(['check', target, '--rules', control.rule, '--json'], {
    stdout: () => {}, stderr: () => {},
  });
  const directory = resolve(root, '.perch/usage');
  let receipt, receiptPath;
  for (const name of (await readdir(directory)).sort().reverse()) {
    const candidate = JSON.parse(await readFile(resolve(directory, name), 'utf8'));
    if (candidate.target === control.path && candidate.at >= started) {
      receipt = candidate; receiptPath = `.perch/usage/${name}`; break;
    }
  }
  const answers = receipt?.answers.filter(a => a.rule === control.rule) ?? [];
  const covered = receipt?.checked > 0 && receipt.provider_responses > 0
    && answers.length > 0 && [0, 3].includes(exit) ? true : false;
  const finding = covered ? receipt.findings.some(f => f.rule === control.rule) : null;
  const row = { ...control, source_sha256: digest(source), receipt: receiptPath,
    rules_sha256: receipt?.rules_sha256, exit, covered, finding,
    correct: covered && finding === (control.expected === 'violates'),
    model: receipt?.resolved_model, elapsed_ms: receipt?.elapsed_ms,
    checked: receipt?.checked, units: receipt?.units,
    probability_broken: covered ? Math.max(...answers.map(a => 1 - a.probability_true)) : null,
    parser: receipt?.parser ?? null };
  rows.push(row);
  console.log(`${control.id}: ${covered ? `${finding ? 'finding' : 'pass'} ${Math.round(row.probability_broken * 100)}%` : 'unavailable'}`);
  if (!covered) break;
}
const report = { schema: 1, started, completed: new Date().toISOString(),
  note: 'Synthetic controls measure only these supplied cases. Held-out sources were frozen before initial calibration; they cease to be unseen after this run. No probabilities are deterministic proof.',
  planned: controls.length, executed: rows.length, covered: rows.filter(r => r.covered).length,
  correct: rows.filter(r => r.correct).length, rows };
await mkdir(dirname(resolve(root, output)), { recursive: true });
await writeFile(resolve(root, output), JSON.stringify(report, null, 2) + '\n');
console.log(`Saved ${output}: ${report.correct}/${report.covered}, planned ${report.planned}`);
if (report.covered !== report.planned || report.correct !== report.covered) process.exitCode = 1;
