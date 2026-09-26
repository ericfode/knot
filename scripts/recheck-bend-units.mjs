#!/usr/bin/env node
// User-requested corpus recheck. Routine changes should use targeted lint instead.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPerch } from './perch-workflow.mjs';
import { analyzeBendSource } from './perch-bend.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
if (!process.argv.includes('--live')) {
  console.error('Use --live for the explicitly requested corpus recheck.');
  process.exit(2);
}
const output = resolve(root, process.argv.find(a => a.startsWith('--output='))?.slice(9)
  ?? 'docs/perch-calibration/bend-units-2026-09-26.json');
const sources = execFileSync('rg', ['--files', 'packages', 'research', '-g', '*.bend'],
  { cwd: root, encoding: 'utf8' }).trim().split('\n').sort();
const packets = execFileSync('rg', ['--files', 'packages', 'research', '-g', 'LAW_REVIEW.md'],
  { cwd: root, encoding: 'utf8' }).trim().split('\n').sort();
const selected = process.argv.find(a => a.startsWith('--paths='))?.slice(8).split(',');
const paths = selected ?? [...sources, ...packets];
const rules = [
  'bend-fuel-completeness', 'bend-machine-arithmetic', 'bend-borrow-lifetime',
  'bend-ordered-f32', 'bend-effect-boundary', 'bend-device-stack',
  'perf-growing-prefix-copy', 'perf-loop-invariant-work',
  'perf-linked-list-indexing', 'perf-amortized-growth',
];
const packetOwnerRules = {
  int_map: 'package-int-map-union-observation',
  output_builder: 'output-builder-linear-assembly',
  term_store: 'term-store-memo-completion-boundary',
  vec: 'vec-logical-state-observation',
};
const report = { schema: 1, started: new Date().toISOString(), planned: paths.length,
  note: 'Actual working-copy parsed Bend declarations plus Markdown law packets. Type-negative fixtures are included and labelled; Perch is not a type/proof gate. Compiler rules have no production src/compiler targets yet.', rows: [] };
await mkdir(dirname(output), { recursive: true });
for (const path of paths) {
  const started = new Date().toISOString();
  const source = await readFile(resolve(root, path));
  if (path.endsWith('.bend')) {
    const analysis = await analyzeBendSource(source.toString());
    if (analysis.parser_status === 'parsed' && analysis.declarations.length === 0) {
      report.rows.push({ path, applicable: false, covered: false,
        parser_status: analysis.parser_status,
        source_sha256: createHash('sha256').update(source).digest('hex'),
        reason: 'Parsed successfully; contains no executable def/law declaration for these method rules.' });
      console.log(`${report.rows.length}/${paths.length} ${path}: no applicable declaration (not a lint pass)`);
      continue;
    }
  }
  const args = ['check', path, '--json'];
  if (path.endsWith('.bend')) args.push('--rules', rules.join(','));
  else if (/^packages\/[^/]+\/(tests\/perch|review)\//.test(path)) {
    const owner = packetOwnerRules[path.split('/')[1]];
    if (!owner) throw new Error(`No intended owner rule for calibration packet ${path}`);
    args.push('--rules', owner);
  }
  const exit = await runPerch(args, { stdout: () => {}, stderr: () => {} });
  let receipt, receiptPath;
  for (const name of (await readdir(resolve(root, '.perch/usage'))).sort().reverse()) {
    const candidate = JSON.parse(await readFile(resolve(root, '.perch/usage', name), 'utf8'));
    if (candidate.target === path && candidate.at >= started) {
      receipt = candidate; receiptPath = `.perch/usage/${name}`; break;
    }
  }
  const source_sha256 = createHash('sha256').update(await readFile(resolve(root, path))).digest('hex');
  const covered = [0, 3].includes(exit) && receipt?.checked > 0
    && receipt.provider_responses > 0 && receipt.provider_requests === receipt.provider_responses
    && receipt.source_sha256 === source_sha256;
  const row = { path, receipt: receiptPath, exit, covered,
    negative_fixture: /\/negative\/|affine_negative|element_negative|affine-(slot|task)-reuse/.test(path),
    ...receipt, source_unchanged: receipt?.source_sha256 === source_sha256 };
  report.rows.push(row);
  report.completed = new Date().toISOString();
  report.covered_files = report.rows.filter(r => r.covered).length;
  report.no_applicable_declarations = report.rows.filter(r => r.applicable === false).length;
  report.units = report.rows.reduce((n, r) => n + (r.units?.length ?? 0), 0);
  report.checked = report.rows.reduce((n, r) => n + (r.checked ?? 0), 0);
  report.findings = report.rows.reduce((n, r) => n + (r.findings?.length ?? 0), 0);
  report.complete = report.covered_files + report.no_applicable_declarations === report.planned;
  await writeFile(output, JSON.stringify(report, null, 2) + '\n');
  console.log(`${report.rows.length}/${paths.length} ${path}: ${receipt?.units?.length ?? 0} units, ${receipt?.checked ?? 0} checks, ${receipt?.findings?.length ?? 0} findings, ${covered ? 'covered' : 'FAILED'}`);
  if (!covered) break;
}
if (!report.complete) process.exitCode = 1;
