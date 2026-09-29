<!-- prechecks packet v1; rule=clause-vs-delta; increment=harness-2; head=364d427ed0df; base=b926a3c379b8; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-bootstrap/README.md@364d427e sha256=ba23aecc2e498f3909e9ccc0678061405f99c8110183dfcb7b8dd4d2466c8f03; tests/compiler-bootstrap/check.py@364d427e sha256=c1507662a6f30eabd6e661932264ed9515effa3b27461dcec9611802d6cd76d4 -->
# Claim
Invariance clause (tests/compiler-bootstrap/README.md):

> Every generation-contract field those files fix is held to the files, never to the receipt's own copy: the argv (from the same builder the harness runs), the maxima, `output_bytes`, whether module loading is in use, the entry, root and target, Node and the seed. Whether a loader audit is due comes from `module_loading.audit_arguments`, not from the receipt.

# Evidence
Evidence: the governed diff hunks (base to head).
```
@@ -97,8 +175,207 @@ def outcome(obs) -> str:
 
 
-def judge(progress) -> list[str]:
-    """Gate verdict over recorded fields: reached stages agree exactly; blocked
-    stages report Unsupported or Exhausted; Knot never calls its own source Invalid."""
-    violations = []
+def detail(obs) -> tuple[str, ...]:
+    """The stderr fields after the classification word."""
+    return tuple(obs['stderr'].rstrip('\n').split('\t')[1:])
+
+
+def exhaustion(obs) -> str | None:
+    """Which budget an Exhausted observation ran out of, from recorded fields
+    only: Knot's own budget (`Exhausted phase budget at`), a runtime budget,
+    or the host's stack, memory or time."""
+    if outcome(obs) != 'Exhausted':
+        return None
+    if obs.get('exit') is None:
+        return 'host-time'
+    if obs.get('host'):
+        return HOST_EXHAUSTION.get(detail(obs), 'host-unclassified')
+    if detail(obs)[1:2] == ('budget',):
+        return 'knot-budget'
+    return RUNTIME_EXHAUSTION.get(detail(obs), 'unclassified')
+
+
+def excuse(row) -> str | None:
+    """Why A2 may stop on the S that C1 built without diverging from C1: a
+    runtime budget C1 lacks, or a harness that cannot run A2 yet."""
+    if exhaustion(row) in RUNTIME_EXHAUSTION.values():
+        return exhaustion(row)
+    if row.get('source') == 'harness' and outcome(row) == 'Unsupported':
+        return PENDING.get(detail(row))
+    return None
+
+
+def after_c1(row) -> str:
+    """e2e3.a3's status when A2 stops on the S that C1 built. C1 built S under
+    the same argv and the same Knot semantics, so a Knot Unsupported, or an
+    exhaustion without an excuse, is A2 diverging from C1: never passing. Any
+    other class stays a blocker, which the judge rejects unless excused."""
+    kind = outcome(row)
+    if excuse(row) or kind not in ALLOWED:
+        return 'blocked'
+    if kind == 'Exhausted':
+        return 'divergent-exhausted'
+    return 'divergent-unsupported' if row.get('source') == 'knot' else 'blocked'
+
+
+def reserved_in(argv, manifest) -> list[str]:
+    return sorted(set(argv) & set(manifest['reserved_flags']['flags']))
+
+
+def invocation(sid, argv) -> list[str]:
+    """The argv a compile step executes under its generation argv (RUNNER)."""
+    return [*RUNNER[sid], *argv]
+
+
+def executed(s) -> dict:
+    """The observation of a step's own run: its result when reached, else its blocker."""
+    return (s.get('result') if s['status'] == 'reached' else s.get('blocker')) or {}
+
+
+def pin_of(place: str, manifest) -> str | None:
+    if place == manifest['base']['path']:
+        return manifest['base']['sha256']
+    if place.startswith(f'{LIB}/'):
+        return manifest['packages'].get(place[len(LIB) + 1:])
+    return None
+
+
+def bundle_problems(bundle, manifest) -> list[str]:
+    """A staged bundle is copied regular single-link files inside its sandbox,
+    Base and every hash package equal to their pins (FX-04, FX-05, A2H-08)."""
+    problems = [f"unresolved imports {bundle['unresolved']}"] if bundle.get('unresolved') else []
+    files = bundle.get('files', {})
+    if sorted(bundle.get('order', [])) != sorted(files):
+        problems.append('closure order and staged files differ')
+    for place, f in files.items():
+        if f.get('kind') != 'regular' or f.get('links') != 1:
+            problems.append(f"{place} is not a regular single-link file ({f.get('kind')}, {f.get('links')} links)")
+        if place.startswith(('/', '../')) or '/../' in place:
+            problems.append(f'{place} escapes the sandbox')
+        pin = pin_of(place, manifest)
+        if pin is None and place.startswith(f'{LIB}/'):
+            problems.append(f'{place} is an unpinned package file')
+        elif pin is not None and f.get('sha256') != pin:
+            problems.append(f'{place} differs from its pin')
+    return problems
+
+
+def contract_problems(c, bundle, contract, manifest) -> list[str]:
+    """One step's contract against src/CONTRACT.json and the manifest, never
+    against its own recorded copy: the one argv over the staged closure, on the
+    qualified host and the pinned runtime."""
+    problems = []
+    argv, maxima, modules = generation_argv(contract, manifest, COMPILER), budgets(contract), modules_advertised(contract)
+    if c['argv'] != argv:
+        problems.append(f"argv {c['argv']} is not the one generation argv {argv}")
+    if c['maxima'] != maxima:
+        problems.append(f"maxima {c['maxima']} are not src/CONTRACT.json maximum_overrides {maxima}")
+    if c['modules'] != modules:
+        problems.append(f"module loading {c['modules']} differs from src/CONTRACT.json ({modules})")
+    if (c['entry'], c['root'], c['target']) != (COMPILER, LIB, target(contract)):
+        problems.append('entry, bundle root or target differs from src/CONTRACT.json')
+    if reserved_in(c['argv'], manifest):
+        problems.append(f"argv uses seed-reserved flags {reserved_in(c['argv'], manifest)}")
+    if bundle is None or c['closure'] != bundle['order'] or c['bundle_sha256'] != digest(canonical(bundle['files'])):
+        problems.append('contract closure or bundle digest differs from the staged sandbox')
+    if c['host']['system'] != manifest['qualified_host']['system']:
+        problems.append(f"host {c['host']['system']} is not the qualified host")
+    node, pinned = c['runtime']['node'], contract['host']['version']
+    if node != pinned or c['runtime']['required_node'] != pinned:
+        problems.append(f"Node {node} is not src/CONTRACT.json's pinned {pinned}")
+    if c['build']['seed'] != contract['seed']:
+        problems.append("build seed differs from src/CONTRACT.json's seed")
+    if c['runtime']['memory_maximum'] != manifest['memory_maximum']:
+        problems.append('memory maximum differs from the manifest (D19)')
+    return problems
+
+
+def audit_problems(audit, contract, bundle, manifest) -> list[str]:
+    """FX-21: under module loading, C1's loader closure (--audit-bundle Module
+    lines) is exactly the staged sandbox, minus Base, which the audit pins
+    instead; or the audit is blocked by an allowed classification. Whether an
+    audit is due comes from src/CONTRACT.json, never from the receipt."""
+    status = audit.get('status')
+    if modules_advertised(contract) and not auditing(contract):
+        return ['src/CONTRACT.json advertises module loading without --audit-bundle']
+    if not auditing(contract):
+        return [] if status == 'unavailable' else ['audit recorded although src/CONTRACT.json advertises no --audit-bundle']
+    if status == 'blocked':
+        kind = outcome(audit['blocker'])
+        return [] if kind in ALLOWED else [f'loader audit blocker is {kind}; only Unsupported or Exhausted may block']
+    if status != 'recorded':
+        return [f'loader audit is {status}; module loading requires a recorded or blocked audit']
+    staged = {x for x in bundle['order'] if x.endswith('.bend') and x != manifest['base']['path']}
+    problems = [] if set(audit['modules']) == staged else [
+        'loader closure (--audit-bundle Module lines) differs from the staged sandbox']
+    if audit['trust']['base_pin'] != [manifest['base']['sha256']]:
+        problems.append('audit BasePin differs from the pinned Base')
+    return problems
+
+
+def generation_problems(p, contract, manifest) -> list[str]:
+    """The generation contract, the staged sandboxes, the loader audit, the
+    artifacts and C1's per-case observations, from recorded fields held to
+    src/CONTRACT.json and the manifest."""
+    problems = []
+    bundles = p.get('bundles', {})
+    for entry, bundle in sorted(bundles.items()):
+        problems += [f'{entry}: {x}' for x in bundle_problems(bundle, manifest)]
+    contracts = p.get('generation_contract', {})
+    if any(sid not in contracts for sid in GENERATIONS):
+        return problems + ['generation contract is missing a step']
+    if contracts[GENERATIONS[0]] != contracts[GENERATIONS[1]]:
+        problems.append('generation contracts differ between e2e3.a2 and e2e3.a3')
+    for sid in GENERATIONS:
+        c = contracts[sid]
+        problems += [f'{sid}: {x}' for x in contract_problems(c, bundles.get(c['entry']), contract, manifest)]
+    by_id = {s['id']: s for s in p['stages']}
+    if by_id['e2e2.compile']['status'] != 'not-run' and by_id['e2e2.compile'].get('args') != generation_argv(
+            contract, manifest, PARSER):
+        problems.append('e2e2.compile: argv is not the one generation argv')
+    for sid, entry in (('e2e2.compile', PARSER), ('e2e3.a2', COMPILER), ('e2e3.a3', COMPILER)):
+        ran, want = executed(by_id[sid]).get('argv'), invocation(sid, generation_argv(contract, manifest, entry))
+        if by_id[sid]['status'] != 'not-run' and ran != want:
+            problems.append(f'{sid}: executed argv {ran} is not {want}')
+    cap, pages = budgets(contract)[-1], manifest['memory_maximum']['pages']
+    for sid in GENERATIONS:
+        s, c = by_id[sid], contracts[sid]
+        if s['status'] != 'not-run' and s.get('args') != c['argv']:
+            problems.append(f'{sid}: argv differs from its generation contract')
+        a = s.get('artifact') if s['status'] == 'reached' else None
+        if a is not None:
+            if a['bytes'] > a['output_bytes'] or a['output_bytes'] != cap:
+                problems.append(f"{sid}: artifact of {a['bytes']} bytes exceeds output_bytes {cap}")
+            problems += [f'{sid}: artifact {x}' for x in memory_problems(a.get('memory'), pages)]
+    problems += audit_problems(p.get('audit', {}), contract, bundles[COMPILER], manifest)
+    c1 = by_id['e2e3.c1']
+    reference = c1.get('observations') or []
+    if len(reference) != c1['corpus']:
+        problems.append('e2e3.c1: per-case observations are missing')
+    conformance = by_id['e2e3.conformance']
+    if conformance['status'] == 'reached':
+        generations = conformance.get('generations') or {}
+        if sorted(generations) != sorted(CONFORMING):
+            problems.append(f'e2e3.conformance: generations {sorted(generations)} are not a2 and a3')
+        for g in CONFORMING:
+            rows = generations.get(g, {}).get('observations', [])
+            first = next((a['file'] for a, b in zip(reference, rows) if a != b), None)
+            if len(rows) != len(reference) or first:
+                problems.append(f"e2e3.conformance: {g} diagnostics differ from C1 at {first or 'the case count'}")
+    seed = p.get('seed_builds', {}).get('C1', {})
+    if seed.get('sha256') is None or seed.get('sha256') != seed.get('repeat_sha256'):
+        problems.append('C1 is not reproducible: two seed builds differ (FX-11)')
+    return problems
+
+
+def judge(progress, contract: Path = ROOT / CONTRACT, manifest: Path = MANIFEST) -> list[str]:
+    """Gate verdict over recorded fields, src/CONTRACT.json and the fixed
+    manifest: reached stages agree exactly; blocked stages report Unsupported or
+    Exhausted; after C1 built S, only an excused stop may block A2; every generation
+    step shares the one contract that src/CONTRACT.json fixes; Knot never calls
+    its own source Invalid. The receipt must name both files by hash."""
+    fixed = {CONTRACT: contract.read_bytes(), f'{REL}/manifest.json': manifest.read_bytes()}
+    violations = [f'receipt was not recorded under this {name}' for name, data in fixed.items()
+                  if progress.get('inputs', {}).get(name) != digest(data)]
+    contract, manifest = (json.loads(fixed[k]) for k in fixed)
     stages = progress.get('stages', [])
     if [(s.get('id'), s.get('tier')) for s in stages] != list(STAGES):

@@ -131,5 +421,5 @@ def judge(progress) -> list[str]:
         if kind not in ('Success', *ALLOWED):
             violations.append(f"{row['path']}: Knot's parser reports its own source {kind} (D4)")
-    return violations
+    return violations + generation_problems(progress, contract, manifest)
 
 
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
