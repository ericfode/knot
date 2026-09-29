<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=literals; head=943104f881da; base=c0bd08d03942; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tools/census/SPEC.md@943104f8 sha256=d72398fb662110dbeb9bee94cb063a85f3bf55bcb7d1f97354bf29ec8a69e6e8; tools/census/census.mjs@943104f8 sha256=df158a987364e93c7f68acb8f4d09219360478601a8c3473493b4df277c1b751 -->
# Claim
tools/census/SPEC.md:43-45 (section: Compiler census contract) - verbatim text:

> A reviewed
> `dependency_feature_exceptions` entry may exempt named features of one exact
> file SHA-256.

# Evidence
Evidence: the declarations the claim names, at head.

`tools/census/census.mjs:218-249` (declaration naming `dependency_feature_exceptions`)
```
  218  export function policyViolations(files, policy) {
  219    const violations = [], byFile = new Map(files.map(f => [f.file, f]));
  220    const dependencies = new Set();
  221    const visit = file => {
  222      if (file === 'Base' || dependencies.has(file)) return;
  223      dependencies.add(file);
  224      const entry = byFile.get(file);
  225      if (!entry) { violations.push(`${file}: missing dependency inventory`); return; }
  226      entry.imports.forEach(i => visit(i.file));
  227      const exception = policy.dependency_feature_exceptions?.[file];
  228      for (const feature of entry.features) {
  229        const pinned = typeof exception?.sha256 === 'string' && exception.sha256 === entry.sha256
  230          && exception.features.includes(feature);
  231        if (policy.forbidden_dependency_features.includes(feature) && !pinned) {
  232          violations.push(`${file}: forbidden dependency feature ${feature}`);
  233        }
  234      }
  235    };
  236    for (const f of files.filter(f => f.file.startsWith('src/'))) {
  237      visit(f.file);
  238      const approved = policy.files[f.file];
  239      if (!approved) violations.push(`${f.file}: unapproved source file`);
  240      for (const i of f.imports) {
  241        if (!approved?.imports.some(a => a.module === i.module && a.file === i.file)) violations.push(`${f.file}: unapproved import ${i.module} -> ${i.file}`);
  242        visit(i.file);
  243      }
  244      for (const d of f.declarations) for (const feature of d.features) {
  245        if (!approved?.declarations[d.id]?.includes(feature)) violations.push(`${d.id}: unapproved feature ${feature}`);
  246      }
  247    }
  248    return sorted(violations);
  249  }
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
