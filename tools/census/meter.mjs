import path from 'node:path';
import { sorted } from './features.mjs';

const STAGES = ['check', 'wasm'];
const lawFile = file => /(?:^|[-_])(LAWS?|PROOF)\.bend$/i.test(path.posix.basename(file));
const origin = file => file === 'Base' ? 'base' : file.startsWith('src/') ? 'compiler' : 'packages';
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;

export function measureClosure(closure, files, evidence) {
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
    declarations.push({ key: entry.key, file: entry.file, origin: origin(entry.file), boundary: entry.boundary,
      features, missing });
  }
  return { roots: closure.roots, closure: { mode: closure.mode, target: closure.target },
    totals: { declarations: declarations.length,
      ...Object.fromEntries(['compiler', 'packages', 'base'].map(o => [o, declarations.filter(d => d.origin === o).length])),
      ...Object.fromEntries(STAGES.map(s => [s, declarations.filter(d => !d.missing[s].length).length])) },
    missing: Object.fromEntries(STAGES.map(s => {
      const counts = new Map();
      for (const d of declarations) for (const feature of d.missing[s]) counts.set(feature, (counts.get(feature) ?? 0) + 1);
      return [s, [...counts].map(([feature, declarations]) => ({ feature, declarations }))
        .sort((a, b) => b.declarations - a.declarations || compare(a.feature, b.feature))];
    })), declarations, excluded };
}

export function selfhostInventory(implementation, closures, accepted) {
  const evidence = Object.fromEntries(STAGES.map(s => [s, new Set(accepted.classes
    .filter(c => c.stages[s].status === 'observed-in-successful-fixtures' && c.stages[s].evidence.length > 0).map(c => c.feature))]));
  return { schema: 1,
    scope: 'Unique declarations from non-law/proof files in the JS runtime/type closure, including package/Base dependencies and per-file import classes.',
    meaning: 'A count means every required feature class has positive frozen fixture evidence at that stage. It is not acceptance of this declaration or a self-hosting result.',
    limits: ['The census does not execute gates; frozen expectations can precede implementation.',
      'Individual witnesses do not establish support for every use or combination of a feature class.',
      'Intrinsic and foreign source features remain visible; this does not qualify their Wasm implementation or host ABI.',
      'Runtime declarations stated as laws in ordinary files, including filled Base functions, remain in the denominator.',
      'Closure is the existing conservative JS seed cut, not flow analysis, template specialization or the full checked source bundle.'],
    evidence_classes: Object.fromEntries(STAGES.map(s => [s, sorted([...evidence[s]])])),
    suite_reports: accepted.reports,
    roots: Object.fromEntries(['compiler', 'frontend'].map(name => [name, measureClosure(closures.roots[name].js, implementation.files, evidence)])) };
}

export function meterSummary(meter) {
  const lines = ['Self-hosting meter — frozen fixture coverage (not self-hosting acceptance)'];
  for (const [name, root] of Object.entries(meter.roots)) {
    const t = root.totals;
    lines.push(`${name}: ${t.declarations} declarations (${t.compiler} compiler, ${t.packages} package, ${t.base} Base)`);
    lines.push(`  check ${t.check}/${t.declarations}; Wasm ${t.wasm}/${t.declarations}`);
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
