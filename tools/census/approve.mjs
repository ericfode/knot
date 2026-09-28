// Extend tools/census/approved.json with the current src inventory. The printed
// summary (new files, declarations, widened classes, imports) is the review
// record: read it and the policy diff before committing. Forbidden dependency
// features remain enforced by census --check.
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const { build } = await import(path.join(root, 'tools/census/census.mjs'));
const policyPath = path.join(root, 'tools/census/approved.json');
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const files = build(root)['implementation.json'].files.filter(f => f.file.startsWith('src/'));
const summary = [];
for (const f of files) {
  const old = policy.files[f.file];
  const fresh = f.imports.map(i => ({ module: i.module, file: i.file }));
  const imports = old && fresh.length === old.imports.length && fresh.every(i => old.imports.some(a => a.module === i.module && a.file === i.file)) ? old.imports : fresh;
  const declarations = Object.fromEntries(f.declarations.map(d => { const prev = old?.declarations[d.id]; return [d.id, prev && d.features.every(x => prev.includes(x)) && prev.every(x => d.features.includes(x)) ? prev : d.features]; }));
  if (!old) summary.push(`NEW FILE ${f.file}: ${f.declarations.length} declarations`);
  else {
    for (const [id, feats] of Object.entries(declarations)) {
      const prev = old.declarations[id];
      if (!prev) summary.push(`new ${id}: ${feats.join(',')}`);
      else { const added = feats.filter(x => !prev.includes(x)); if (added.length) summary.push(`widen ${id}: +${added.join(',')}`); }
    }
    for (const id of Object.keys(old.declarations)) if (!declarations[id]) summary.push(`gone ${id}`);
    for (const i of imports) if (!old.imports.some(a => a.module === i.module && a.file === i.file)) summary.push(`import ${f.file}: ${i.module} -> ${i.file}`);
  }
  policy.files[f.file] = { imports, declarations };
}
policy.files = Object.fromEntries(Object.entries(policy.files).filter(([k]) => files.some(f => f.file === k)));
fs.writeFileSync(policyPath, JSON.stringify(policy, null, 2) + '\n');
console.log(summary.join('\n'));
