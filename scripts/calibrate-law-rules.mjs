#!/usr/bin/env node
// Explicit, paid calibration of the shared controls. Offline gates never call this.
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPerch } from './perch-workflow.mjs';

if (!process.argv.includes('--live')) {
  console.error('Explicit live invocation required: node scripts/calibrate-law-rules.mjs --live');
  process.exit(2);
}
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const digest = data => createHash('sha256').update(data).digest('hex');
const source = await readFile(join(root, 'tests/perch-laws/cases.json'));
const cases = JSON.parse(source);
const temporary = await mkdtemp(join(root, 'tests/perch-laws/.calibration-'));
const started = new Date().toISOString();
const output = process.argv.find(arg => arg.startsWith('--output='))?.slice(9)
  ?? `docs/perch-calibration/laws-${started.slice(0, 10)}.json`;
const rows = [];
try {
  for (const control of cases) {
    const target = relative(root, join(temporary, control.id, 'LAW_REVIEW.md'));
    const packet = `# Synthetic law calibration: ${control.id}\n\n${control.packet}\n`;
    await mkdir(dirname(join(root, target)), { recursive: true });
    await writeFile(join(root, target), packet);
    const exit = await runPerch(['check', target, '--rules', control.rule, '--json'], {
      stdout: () => {}, stderr: () => {},
    });
    const directory = join(root, '.perch/usage');
    let receipt, receiptPath;
    for (const name of (await readdir(directory)).sort().reverse()) {
      const candidate = JSON.parse(await readFile(join(directory, name), 'utf8'));
      if (candidate.target === target) {
        receipt = candidate;
        receiptPath = `.perch/usage/${name}`;
        break;
      }
    }
    const covered = receipt?.checked === 1 && receipt.provider_responses > 0
      && [0, 3].includes(exit);
    const finding = covered ? receipt.findings.some(f => f.rule === control.rule) : null;
    const row = { id: control.id, rule: control.rule, split: control.split,
      expected: control.expected, packet_sha256: digest(packet), receipt: receiptPath,
      rules_sha256: receipt?.rules_sha256,
      exit, covered, finding, correct: covered && finding === (control.expected === 'violates'),
      model: receipt?.resolved_model,
      probability_broken: receipt?.answers.find(a => a.rule === control.rule)
        ? 1 - receipt.answers.find(a => a.rule === control.rule).probability_true : null };
    rows.push(row);
    console.log(`${row.id} ${row.rule} ${row.split}: ${covered ? finding ? 'finding' : 'pass' : 'unavailable'}; expected ${row.expected}`);
    // Do not hammer an unavailable or rejected credential.
    if (!covered) break;
  }
} finally {
  await rm(temporary, { recursive: true, force: true });
  const report = { schema: 1, started, completed: new Date().toISOString(),
    cases_sha256: digest(source),
    note: 'Synthetic controls measure these supplied cases only. Held-out labels identify the original split, not unseen cases after this run. Reconstruct each input as the heading plus packet in cases.json; temporary files are removed.',
    planned: cases.length, executed: rows.length,
    covered: rows.filter(r => r.covered).length,
    correct: rows.filter(r => r.correct).length, rows };
  await mkdir(dirname(resolve(root, output)), { recursive: true });
  await writeFile(resolve(root, output), JSON.stringify(report, null, 2) + '\n');
  console.log(`Saved ${output}: ${report.correct}/${report.covered} covered controls classified correctly.`);
  if (report.covered !== report.planned || report.correct !== report.covered) process.exitCode = 1;
}
