import path from 'node:path';
import { sorted } from './features.mjs';

const STAGES = ['check', 'wasm'];
const lawFile = file => /(?:^|[-_])(LAWS?|PROOF)\.bend$/i.test(path.posix.basename(file));
const origin = file => file === 'Base' ? 'base' : file.startsWith('src/') ? 'compiler' : 'packages';
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;

export function measureClosure(closure, files, evidence, requirements = { check: new Set(), wasm: new Set() }) {
  if (closure.unresolved.length) throw new Error('Cannot meter an unresolved closure');
  if (new Set(closure.entries.map(e => e.key)).size !== closure.entries.length) throw new Error('Duplicate meter declaration');
  const byFile = new Map(files.map(f => [f.file, f])), declarations = [], excluded = [];
  for (const entry of [...closure.entries].sort((a, b) => compare(a.key, b.key))) {
    const file = byFile.get(entry.file);
    if (!file) throw new Error(`Missing meter file: ${entry.file}`);
    const matches = file.declarations.filter(d => d.key === entry.key);
    if (!matches.length) throw new Error(`Missing meter declaration: ${entry.key}`);
    if (lawFile(entry.file)) {
      excluded.push({ key: entry.key, file: entry.file, reason: 'law/proof source' });
      continue;
    }
    const features = sorted([...file.imports.map(i => i.feature), ...matches.flatMap(d => d.features)]);
    const missing = Object.fromEntries(STAGES.map(stage => [stage, features.filter(f => !evidence[stage].has(f))]));
    const missing_requirements = Object.fromEntries(STAGES.map(stage => [stage, missing[stage].filter(f => !requirements[stage].has(f))]));
    declarations.push({ key: entry.key, file: entry.file, origin: origin(entry.file), boundary: entry.boundary,
      features, missing, missing_requirements });
  }
  const ranked = key => Object.fromEntries(STAGES.map(s => {
    const counts = new Map();
    for (const d of declarations) for (const feature of d[key][s]) counts.set(feature, (counts.get(feature) ?? 0) + 1);
    return [s, [...counts].map(([feature, declarations]) => ({ feature, declarations }))
      .sort((a, b) => b.declarations - a.declarations || compare(a.feature, b.feature))];
  }));
  return { roots: closure.roots, closure: { mode: closure.mode, target: closure.target },
    totals: { declarations: declarations.length,
      ...Object.fromEntries(['compiler', 'packages', 'base'].map(o => [o, declarations.filter(d => d.origin === o).length])),
      ...Object.fromEntries(STAGES.map(s => [s, declarations.filter(d => !d.missing[s].length).length])),
      covered_by_requirements: Object.fromEntries(STAGES.map(s => [s, declarations.filter(d => !d.missing_requirements[s].length).length])) },
    missing: ranked('missing'), missing_requirements: ranked('missing_requirements'), declarations, excluded };
}

export function selfhostInventory(implementation, closures, accepted) {
  const evidence = Object.fromEntries(STAGES.map(s => [s, new Set(accepted.classes
    .filter(c => c.stages[s].status === 'observed-in-successful-fixtures' && c.stages[s].evidence.length > 0).map(c => c.feature))]));
  const requirements = Object.fromEntries(STAGES.map(s => [s, new Set(accepted.requirements.classes
    .filter(c => c.stages[s].fixtures.length > 0).map(c => c.feature))]));
  return { schema: 2,
    scope: 'Unique declarations from non-law/proof files in the JS runtime/type closure, including package/Base dependencies and per-file import classes.',
    meaning: 'Evidenced counts require every class to have a successful fixture in a suite with its mapped registered gate. Covered-by-requirements counts include that evidence plus frozen ungated requirements. Neither is declaration acceptance or a self-hosting result.',
    limits: ['The census inventories registered gate expectations, not fresh execution receipts; ungated expectations remain requirements.',
      'Individual witnesses do not establish support for every use or combination of a feature class.',
      'Intrinsic and foreign source features remain visible; this does not qualify their Wasm implementation or host ABI.',
      'Runtime declarations stated as laws in ordinary files, including filled Base functions, remain in the denominator.',
      'Closure is the existing conservative JS seed cut, not flow analysis, template specialization or the full checked source bundle.'],
    evidence_classes: Object.fromEntries(STAGES.map(s => [s, sorted([...evidence[s]])])),
    requirements: { suites: accepted.requirements.suites, classes: accepted.requirements.classes },
    suite_reports: accepted.reports,
    roots: Object.fromEntries(['compiler', 'frontend'].map(name => [name, measureClosure(closures.roots[name].js, implementation.files, evidence, requirements)])) };
}

export function meterSummary(meter) {
  const lines = ['Self-hosting meter — evidence and frozen requirements (not self-hosting acceptance)'];
  for (const [name, root] of Object.entries(meter.roots)) {
    const t = root.totals;
    lines.push(`${name}: ${t.declarations} declarations (${t.compiler} compiler, ${t.packages} package, ${t.base} Base)`);
    lines.push(`  evidenced now: check ${t.check}/${t.declarations}; Wasm ${t.wasm}/${t.declarations}`);
    lines.push(`  covered by frozen requirements (including evidenced): check ${t.covered_by_requirements.check}/${t.declarations}; Wasm ${t.covered_by_requirements.wasm}/${t.declarations}`);
    for (const s of STAGES) {
      const missing = root.missing[s];
      const top = missing.slice(0, 5).map(m => `${m.feature} ${m.declarations}`).join(', ') || 'none';
      lines.push(`  ${s} blockers: ${top}${missing.length > 5 ? ` (+${missing.length - 5} classes)` : ''}`);
    }
  }
  const unknown = meter.suite_reports.filter(r => r.status.startsWith('unrecognized'));
  lines.push(`Unrecognized suite/manifests: ${unknown.length}. Full rankings and declaration gaps: docs/compiler-campaign/inventory/selfhost.json`);
  return lines.join('\n');
}
