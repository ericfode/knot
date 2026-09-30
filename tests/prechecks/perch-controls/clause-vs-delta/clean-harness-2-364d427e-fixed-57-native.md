<!-- prechecks packet v1; rule=clause-vs-delta; increment=harness-2; head=364d427ed0df; base=b926a3c379b8; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-bootstrap/README.md@364d427e sha256=ba23aecc2e498f3909e9ccc0678061405f99c8110183dfcb7b8dd4d2466c8f03 -->
# Claim
Invariance clause at base (tests/compiler-bootstrap/README.md), reworded or removed by this branch:

> It is fixed at 57 cases. - C1 is built only in the native lane.

# Evidence
Evidence: the document change that rewords or removes the clause (unified diff, base to head).
```diff
@@ -25,10 +36,10 @@ never count.
 | --- | --- | --- |
-| `e2e2.reference` | The seed builds `src/parse-cli.bend` (native and Bun). Both run on every corpus file. | Both lanes agree byte for byte on every file. |
-| `e2e2.compile` | C1 compiles `src/parse-cli.bend` and its imports to a parser module. | It prints `Built` with an artifact of that size. |
+| `e2e2.reference` | The seed builds `src/parse-cli.bend` (native and Bun) from its sandbox. Both run on every corpus file. | Both lanes agree byte for byte on every file. |
+| `e2e2.compile` | C1 compiles `src/parse-cli.bend` inside the parser sandbox, with the generation argv. | It prints `Built` with an artifact of that size. |
 | `e2e2.self-parse` | The parser module runs on the same corpus through `host.mjs`. | Exit, stdout and stderr are byte-identical to the reference on every file. |
-| `e2e3.c1` | The seed builds C1 from `src/compile-cli.bend` (native). C1 compiles the conformance corpus. | Every program and reject matches. |
-| `e2e3.a2` | C1 compiles S (`src/compile-cli.bend` and its imports) to A2. | It prints `Built` with an artifact. |
-| `e2e3.a3` | A2 compiles the same S to A3 under `host.mjs`. | It builds A3. |
+| `e2e3.c1` | The seed builds C1 from the S sandbox (native, twice). C1 compiles the conformance corpus. | Every program and reject matches. |
+| `e2e3.a2` | C1 compiles S inside the S sandbox, with the generation argv. | It prints `Built` with an artifact within `output_bytes`. |
+| `e2e3.a3` | A2 compiles the same S under `host.mjs`, inside a fresh copy of the sandbox, with the same argv. | It builds A3. A2 may stop here only with an excuse (see [A2 after C1 built S](#a2-after-c1-built-s)); otherwise the stop is `divergent-exhausted` or `divergent-unsupported`, which never pass. |
 | `e2e3.fixpoint` | A2 and A3 are compared. | They are byte-identical. |
-| `e2e3.conformance` | A2 and A3 each compile the conformance corpus. | Every call tag and rejection matches, and every module is byte-identical to C1's. |
+| `e2e3.conformance` | A2 and A3 each compile the conformance corpus. | Every call tag and rejection matches, every module is byte-identical to C1's, and every `(exit, stdout, stderr)` equals C1's byte for byte. |
 
@@ -175,14 +468,28 @@ adapter's hash joins the receipt's `inputs`.
 - The conformance corpus uses the enum profile (`knot-enum-1`). It is fixed
-  at 57 cases.
+  at 57 cases, and it runs from the repository root, not from a sandbox.
 - C1 is built only in the native lane. The Bun lane's memory fault on large
   modules is a known open note in the campaign state.
-- A seed build failure is a harness failure (exit 1), not a stage result. A
-  clang flake in the native lane is surfaced, not retried.
+- A seed build failure, a pin mismatch, a non-Darwin host or another Node is a
+  harness failure (exit 1), not a stage result. A clang flake in the native lane
+  is surfaced, not retried.
+- The excuses name the IO host's current rendering of `exhausted(kind)` (`io
+  steps`, `io memory`, `io frames`). `io memory` also covers the host's 16 MiB
+  transfer cap, which C1 lacks as well. When the VM route renders its budgets
+  differently, add the new shapes to `RUNTIME_EXHAUSTION`; until then they are
+  `unclassified` and fail the verdict.
+- The host-memory tag rests on V8's error messages. This host allocates a
+  4 GiB memory without failing, so no real allocation failure is exercised;
+  the classification control feeds the messages to `trap` directly.
+- The audit cannot cross-check S until S loads: on the modules merge it stops at
+  the same lexer blocker. The audit control exercises the comparator meanwhile.
+- The generation contract qualifies only Darwin. Other hosts fail before staging.
 - The per-stage budgets are 600 seconds for each compile and 600 seconds for
-  each host request. Together they can exceed the gate runner's default
-  900-second per-gate timeout. Today the gate takes about 30 seconds. Once
-  self-compiles become slow, raise `--timeout`, so that a stage's `Exhausted`
-  is recorded rather than the runner 
```

Evidence: the changed code regions that share the most words with the clause.
```
@@ -29,9 +42,11 @@ SEED = 'scripts/bend-reference'
 HOST = f'{REL}/host.mjs'
 RUN_WASM = 'scripts/run-wasm.mjs'
+MANIFEST = HERE / 'manifest.json'
 PROGRESS = HERE / 'receipts/progress.json'
+CONTRACT = 'src/CONTRACT.json'
 REFERENCE = HERE / 'receipts/reference.json'
-BASE = '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend'
 PARSER = 'src/parse-cli.bend'      # E2E-2 subject
 COMPILER = 'src/compile-cli.bend'  # the one compiler entry for C1, A2 and A3
+CHECKER = 'src/check-cli.bend'    # the loader audit (--audit-bundle), built only when advertised
 PROGRAMS = 'tests/compiler-wasm/cases.json'
 REJECTS = 'tests/compiler-checker/cases.json'

@@ -42,5 +57,21 @@ STAGES = (('e2e2.reference', 'E2E-2'), ('e2e2.compile', 'E2E-2'), ('e2e2.self-pa
           ('e2e3.c1', 'E2E-3'), ('e2e3.a2', 'E2E-3'), ('e2e3.a3', 'E2E-3'),
           ('e2e3.fixpoint', 'E2E-3'), ('e2e3.conformance', 'E2E-3'))
-SECONDS = {'parse': 60, 'compile': 600, 'host': 600, 'call': 60}
+GENERATIONS = ('e2e3.a2', 'e2e3.a3')  # C1 -> A2 and A2 -> A3: one contract
+# What each compile step executes before its argv: C1 is a process run from the
+# step's sandbox, a sibling of BUILD/c1; A2 is a host guest, handed the argv itself.
+RUNNER = {'e2e2.compile': ['../c1'], 'e2e3.a2': ['../c1'], 'e2e3.a3': []}
+CONFORMING = ('a2', 'a3')  # the generations that run the conformance corpus against C1
+LIB = 'lib'              # the relative bundle ROOT inside every sandbox
+OUTPUT = 'generation.wasm'  # the one output operand of every generation step
+MAGIC = b'\0asm\x01\0\0\0'
+SANDBOX = {COMPILER: 'bundle', PARSER: 'parser-bundle', CHECKER: 'checker-bundle'}
+# Exhausted observations the host makes itself, by (phase, code).
+HOST_EXHAUSTION = {('wasm', 'call-stack'): 'host-stack', ('wasm', 'memory'): 'host-memory'}
+# Budgets a generation's runtime declares and C1's native lane lacks, as the IO
+# host renders exhausted(kind): D16 fuel and frame region, D19 heap.
+RUNTIME_EXHAUSTION = {('io', 'steps'): 'vm-fuel', ('io', 'memory'): 'vm-heap', ('io', 'frames'): 'vm-frames'}
+# Unsupported results of a harness that cannot run a generation yet (host.mjs).
+PENDING = {('host', code): f'harness-{code}' for code in ('io-abi-pending', 'abi-unrecognized')}
+DIVERGENT = ('divergent-exhausted', 'divergent-unsupported')
 
 

@@ -286,6 +816,13 @@ def module_runner(module: Path, label, inputs=None):
 
 
-def conformance(compile_one, reference_modules=None) -> dict:
-    """The existing gate corpus: seed-derived call tags and fixed rejections."""
+def observed(file, obs) -> dict:
+    """One conformance case's full observation; later generations must repeat C1's byte for byte (FX-18)."""
+    row = {'file': file, 'exit': obs['exit'], 'stdout': text(obs['stdout']), 'stderr': text(obs['stderr'])}
+    return {**row, 'outcome': obs['outcome']} if 'outcome' in obs else row
+
+
+def conformance(compile_one, reference=None) -> dict:
+    """The existing gate corpus: seed-derived call tags and fixed rejections.
+    Against a C1 reference, modules and observations must also equal C1's."""
     programs = json.loads((ROOT / PROGRAMS).read_bytes())['cases']
     rejects = [c for c in json.loads((ROOT / REJECTS).read_bytes())['cases'] if c['knot']['exit'] != 0]

@@ -399,5 +1000,5 @@ def controls(names, native, bun) -> list[dict]:
             ('host-io-seam', importing_module(),
              {'abi': 'knot-io', 'outcome': 'Unsupported' if not (HERE / 'io-abi.mjs').exists() else None}),
-            ('host-invalid-module', b'\0asm\x01\0\0\0\xff', {'abi': None, 'outcome': 'HostFailure'})):
+            ('host-invalid-module', MAGIC + b'\xff', {'abi': None, 'outcome': 'HostFailure'})):
         module = folder / f'{label}.wasm'
         module.write_bytes(data)

@@ -411,9 +1121,51 @@ def controls(names, native, bun) -> list[dict]:
 # --------------------------------------------------------------- mutants
 
-def mutants(progress) -> list[dict]:
-    """Scratch copies with substituted recorded classifications; the judge must reject each."""
+def reached_chain(progress) -> dict:
+    """The judge's positive control: the real receipt with every E2E-3 stage
+    reached as a correct fixpoint would record it. The generation rules only
+    bite on reached generations, which the current tree does not have."""
+    p = copy.deepcopy(progress)
+    c = p['generation_contract'][GENERATIONS[0]]
+    by = {s['id']: s for s in p['stages']}
+    rows, size = by['e2e3.c1']['observations'], 4096
+    made = {'sha256': digest(b'fixpoint'), 'bytes': size, 'output_bytes': c['target']['output_bytes'],
+            'headroom_bytes': c['target']['output_bytes'] - size, 'memory': wasm_memories(memory_probes()['knot-shape'])}
+
+    def compiled(sid):
+        return stage(sid, status='reached', corpus=1, agree=1, disagree=0, args=list(c['argv']),
+                     result={'argv': invocation(sid, c['argv']), 'exit': 0, 'stdout': f'Built\t{size}\n', 'stderr': ''},
+                     artifact=dict(made))
+    by['e2e3.a2'], by['e2e3.a3'] = map(compiled, GENERATIONS)
+    by['e2e3.fixpoint'] = stage('e2e3.fixpoint', status='reached', corpus=1, agree=1, disagree=0)
+    by['e2e3.conformance'] = stage('e2e3.conformance', status='reached', corpus=2 * len(rows), agree=2 * len(rows),
+                                   disagree=0, generations={g: {'agree': len(rows), 'disagree': 0, 'first_disagreement': None,
+                                                                'observations': copy.deepcopy(rows)} for g in CONFORMING})
+    p['stages'] = [by[sid] for sid, _ in STAGES]
+    return p
+
+
+def mutants(progress, contract, manifest) -> list[dict]:
+    """Scratch copies with substituted recorded fields; the judge must reject
+    each for its named reason. The `real` cases mutate the real receipt; the
+    `chain` cases mutate the reached chain, whose unmutated copies must pass. A case
+    may be judged under src/CONTRACT.json with module loading advertised
+    ('modules') or withdrawn ('single'); its receipt then names that file."""
     folder = ROOT / BUILD / 'judge'
     folder.mkdir(parents=True, exist_ok=True)
 
+    def variant(modules: bool) -> Path:
+        c = copy.deepcopy(contract)
+        arguments = c['compiler']['arguments'].removeprefix('[--bundle ROOT] ')
+        c['compiler']['arguments'] = '[--bundle ROOT] ' * modules + arguments
+        loading = c.setdefault('module_loading', {})
+        if modules:
+            loading.setdefault('audit_arguments', '--audit-bundle ROOT source')
+        else:
+            loading.pop('audit_arguments', None)
+        path = folder / f"contract-{'modules' if modules else 'single'}.json"
+        path.write_text(json.dumps(c, indent=2) + '\n')
+        return path
+    variants = {'modules': variant(True), 'single': variant(False)}
+
     def knot_blocker(p):
         s = next((s for s in p['stages'] if s['status'] == 'blocked' and s['blocker']['source'] == 'knot'), None)

@@ -520,4 +1526,5 @@ def main() -> int:
         reference_bytes = json.dumps(reference, indent=2).encode() + b'\n'
         progress['corpus'] = {'files': len(names), 'reference_sha256': digest(reference_bytes)}
+        # A Bun-lane fault counts as a disagreement here, never as exhaustion: both oracle lanes must agree.
         stages = [stage('e2e2.reference', status='reached', corpus=len(names), agree=lanes['agree'],
                         disagree=lanes['disagree'] + lanes['exhausted'], lanes=['native', 'bun'],

@@ -543,31 +1552,49 @@ def main() -> int:
                     first = t['first_exhausted']
                     stages.append(stage('e2e2.self-parse', status='blocked', exhausted=t['exhausted'],
-                                        blocker={'source': 'knot', **first}, **fields))
+                                        blocker=tagged({'source': 'knot', **first}), **fields))
                 else:
                     stages.append(stage('e2e2.self-parse', status='reached', exhausted=t['exhausted'], **fields))
 
         # E2E-3: seed -> C1 -> A2 -> A3. C1 must already pass the conformance corpus.
-        base = conformance(lambda source, out: run([*c1, source, out.relative_to(ROOT).as_posix()], SECONDS['compile']))
+        base = conformance(lambda source, out: run([f'./{BUILD}/c1', source, out.relative_to(ROOT).as_posix()],
+                                                   SECONDS['compile']))
         cases = base['programs'] + base['rejects']
         stages.append(stage('e2e3.c1', status='reached', corpus=cases, agree=base['agree'], disagree=base['disagree'],
                             lane='native', first_disagreement=base['first_disagreement'],
                             programs=base['programs'], calls=base['calls'], rejects=base['rejects'],
-                            modules=base['modules']))
-        a2, a3 = ROOT / BUILD / 'a2.wasm', ROOT / BUILD / 'a3.wasm'
-        stage_a2 = compile_stage('e2e3.a2', c1, COMPILER, a2)
+                            modules=base['modules'], observations=base['observations']))
+        a2, a3 = build / 'a2.wasm', build / 'a3.wasm'
+        stage_a2, c1_on_s = compile_stage('e2e3.a2', sandbox, bundle, manifest, contracts['e2e3.a2']['argv'], a2, cap)
         stages.append(stage_a2)
+        # A2 runs in a fresh copy of the same sandbox, under a contract built the same way.
+        sandbox_a2 = build / f"{SANDBOX[COMPILER]}-a2"
+        replica(sandbox, sandbox_a2, bundle)
+        verify(sandbox_a2, bundle, manifest)
+        contracts['e2e3.a3'] = generation_contract(contract, manifest, bundle, sandbox_a2, shared)
+        progress['generation_contract'] = contracts
+        measured = {}
         if stage_a2['status'] != 'reached' or stage_a2['disagree']:
             stages += [not_run('e2e3.a3', 'e2e3.a2', 1), not_run('e2e3.fixpoint', 'e2e3.a3', 1),
                        not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
         else:
-            got = module_runner(a2, 'a3', list(progress['bundles'][COMPILER]['files']))(COMPILER, a3)
-            if got.get('blocked'):
-                stages.append(blocked('e2e3.a3', got.pop('source'), got, 1))
-            elif got['exit'] != 0:
-                stages.append(blocked('e2e3.a3', 'knot', got, 1))
+            measured['e2e3.a2'] = {k: c1_on_s[k] for k in ('elapsed_seconds', 'peak_rss_bytes')}
+            argv = contracts['e2e3.a3']['argv']
+            answer, result = host(a2, [{'argv': invocation('e2e3.a3', argv), 'inputs': bundle['order'],
+                                        'outputs': [OUTPUT]}], 'a3', cwd=sandbox_a2)
+            verify(sandbox_a2, bundle, manifest)
+            a3.unlink(missing_ok=True)
+            answered = answer is not None and not answer['blocked']
+            got = result[0] if answered else result
+            if answered:
+                measured['e2e3.a3'] = {k: got[k] for k in ('elapsed_seconds', 'peak_rss_bytes')}
+                if OUTPUT in got['files']:
+                    a3.write_bytes(got['files'][OUTPUT])
+            failed = a3_stopped(answer, got, argv)
+            if failed:
+                stages.append(failed)
             else:
                 ok = built(got, a3)
                 stages.append(stage('e2e3.a3', status='reached', corpus=1, agree=int(ok), disagree=int(not ok),
-                                    result=shown(got), artifact_sha256=digest(a3.read_bytes()) if a3.is_file() else None))
+                                    args=argv, result=shown(got), artifact=artifact(a3, cap) if a3.is_file() else None))
             if stages[-1]['status'] != 'reached' or stages[-1]['disagree']:
                 stages += [not_run('e2e3.fixpoint', 'e2e3.a3', 1), not_run('e2e3.conformance', 'e2e3.a3', 2 * cases)]
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
