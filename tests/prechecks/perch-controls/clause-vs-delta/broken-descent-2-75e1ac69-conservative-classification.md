<!-- prechecks packet v1; rule=clause-vs-delta; increment=descent-2; head=75e1ac69852c; base=57a0c01df87f; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-recursion/SPEC.md@75e1ac69 sha256=73ce775985d307efdadb2bf3ff82f2873279fc71fcc5a3579d83b21b88202f8a -->
# Claim
Invariance clause at base (tests/compiler-recursion/SPEC.md), reworded or removed by this branch:

> The task's stated general-recursion behavior is not observed at this pin; Knot's requested conservative classification stays unchanged.

# Evidence
Evidence: the document change that rewords or removes the clause (unified diff, base to head).
```diff
@@ -36,8 +23,11 @@ are fixed independently in the manifest, not converted by a host evaluator.
 
-The seed at `574b6d39a235b539eb19a5c532993a0abb3d11ad` rejects the specified
-nondecreasing calls with a decreasing-self-call diagnostic. It accepts
-lexicographic descent on a later parameter (`second-descent`), which this rule
-deliberately reports Unsupported. The task's stated general-recursion behavior
-is not observed at this pin; Knot's requested conservative classification stays
-unchanged. Negative reference programs are checked only, never evaluated.
+The seed at `574b6d39a235b539eb19a5c532993a0abb3d11ad` rejects
+`same-parameter`, `other-parameter`, `rebuilt-parent`, `rebuilt-constructor`,
+`computed` and `shadow-let` with a decreasing-self-call diagnostic. It accepts
+`second-descent` and evaluates its entry to `1n`. These transitions were refrozen
+before implementation in `../compiler-descent/receipts/reference.json`.
+`expectation-revisions.json` lists each explicitly migrated assertion. The gate
+first verifies the original immutable freeze, then applies only revisions that
+exactly match the independent new freeze (with the original enum compiler's
+field-capability rejection). Neither historical receipt is rewritten.
 
```

Evidence: the changed code regions that share the most words with the clause.
```
`src/descent-LAWS.bend:81-86` (added)
   81  law computed_alias_stays_opaque:
   82    for +token: S.Token
   83    for args: List<&2,C.Term>
   84    {D.shape(8n,C.Reference{token,2,0},Nil{},[D.Alias{2,C.Application{token,0,0,args}}]) ==
   85      Done{D.Opaque{}} : Result<S.Error,D.Shape>}
   86  

`src/descent-PROOF.bend:29-29` (added)
   29  def L.computed_alias_stays_opaque(token,args): {==}

@@ -117,12 +118,14 @@ law erased_alias_stays_erased:
   for +alias: S.Token
   for +known: Maybe<&2,C.Term>
-  {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]},alias,1,2,[flag()]) ==
-    Done{E.Scope{[C.Binding{alias,1,0,0,True{},known},C.Binding{name,1,0,0,True{},known}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}
+  for +aliases: List<&2,D.Alias>
+  {M.alias(E.Scope{[C.Binding{name,1,0,0,True{},known}],2,[1],True{},aliases},alias,1,2,[flag()]) ==
+    Done{E.Scope{[C.Binding{alias,1,0,0,True{},known},C.Binding{name,1,0,0,True{},known}],2,[1],True{},aliases}} : Result<S.Error,E.Scope>}
 
 law alias_preserves_descent_and_identity:
   for +name: S.Token
   for +alias: S.Token
-  {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]},alias,1,1,[flag()]) ==
-    Done{E.Scope{[C.Binding{alias,1,1,0,True{},None{}},C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},[1]}} : Result<S.Error,E.Scope>}
+  for +aliases: List<&2,D.Alias>
+  {M.alias(E.Scope{[C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},aliases},alias,1,1,[flag()]) ==
+    Done{E.Scope{[C.Binding{alias,1,1,0,True{},None{}},C.Binding{name,1,1,0,True{},None{}}],2,[1],True{},aliases}} : Result<S.Error,E.Scope>}
 
 # Exhaustiveness at each split: every declaration absent from the explicit

diff --git a/src/matrix-PROOF.bend b/src/matrix-PROOF.bend
index a89ac9b2..ace63ccf 100644
--- a/src/matrix-PROOF.bend
+++ b/src/matrix-PROOF.bend
@@ -68,6 +68,6 @@ def L.lowering_work_exhaustion(token,columns,rows,types,scope): {==}
 def L.irrefutable_lowering_selects_first(): {==}
 def L.exhaustive_matrix_has_no_missing_branch(): {==}
-def L.erased_alias_stays_erased(name,alias,known): {==}
-def L.alias_preserves_descent_and_identity(name,alias): {==}
+def L.erased_alias_stays_erased(name,alias,known,aliases): {==}
+def L.alias_preserves_descent_and_identity(name,alias,aliases): {==}
 
 def L.default_completes_missing_branch(name,fields,ctors,explicit,absent):

diff --git a/src/recursion-LAWS.bend b/src/recursion-LAWS.bend
index 25ea181d..6fae4bf8 100644
--- a/src/recursion-LAWS.bend
+++ b/src/recursion-LAWS.bend
@@ -6,56 +6,12 @@ import ./patterns.bend as P
 import ./check.bend as K
 import ./eval.bend as V
+import ./descent.bend as D
 
 # Scope and call boundaries; these are not a general termination theorem.
-law root_fields_are_smaller:
-  for +fields: List<&2,U32>
-  for +smaller: List<&2,U32>
-  {E.descendants(0,fields,smaller) == List.append(&2,U32,fields,smaller) : List<&2,U32>}
+def parameter(+token: S.Token, level: U32, known: Maybe<&2,C.Term>) -> C.Binding:
+  C.Binding{token,level,1,0,True{},known}
 
-law descendant_fields_are_smaller:
-  for +fields: List<&2,U32>
-  {E.descendants(2,fields,[2,1]) == List.append(&2,U32,fields,[2,1]) : List<&2,U32>}
-
-law unrelated_fields_stay_unmarked:
-  for fields: List<&2,U32>
-  {E.descendants(3,fields,[2,1]) == [2,1] : List<&2,U32>}
-
-law marked_reference_descends:
-  for token: S.Token
-  for type_id: U32
-  for tail: List<&2,C.Term>
-  {E.descends(Con{C.Reference{token,2,type_id},tail},[2,1]) == True{} : Bool}
-
-law root_reference_does_not_descend:
-  for token: S.Token
-  for type_id: U32
-  for tail: List<&2,C.Term>
-  {E.descends(Con{C.Reference{token,0,type_id},tail},[2,1]) == False{} : Bool}
-
-law rebuilt_argument_does_not_descend:
-  for token: S.Token
-  for type_id: U32
-  for tag: U32
-  for params: List<&2,C.Parameter>
-  for args: List<&2,C.Term>
-  for smaller: List<&2,U32>
-  {E.descends([C.Construct{token,type_id,tag,params,args}],smaller) == False{} : Bool}
-
-law computed_argument_does_not_descend:
-  for token: S.Token
-  for index: U32
-  for type_id: U32
-  for args: List<&2,C.Term>
-  for smaller: List<&2,U32>
-  {E.descends([C.Application{token,index,type_id,args}],smaller) == False{} : Bool}
-
-law empty_call_does_not_descend:
-  for smaller: List<&2,U32>
-  {E.descends(Nil{},smaller) == False{} : Bool}
-
-law later_argument_cannot_establish_descent:
-  for +token: S.Token
-  for +type_id: U32
-  {E.descends([C.Reference{token,0,type_id},C.Reference{token,1,type_id}],[1]) == False{} : Bool}
+def successor(+token: S.Token, level: U32) -> C.Term:
+  C.Construct{token,0,1,[C.Parameter{token,1,0}],[C.Reference{token,level,0}]}
 
 law local_binding_preserves_descent:

`tests/compiler-descent/check.py:375-423` (added)
  375  def main():
  376      BUILD.mkdir(parents=True, exist_ok=True)
  377      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  378      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
  379                'profile': 'knot-fields-wasm-1', 'builds': [], 'proofs': [], 'fixtures': [],
  380                'mutants': [], 'bounds': [], 'resources': []}
  381      try:
  382          manifest = json.loads((HERE / 'expectations.json').read_text())
  383          cases = validate_manifest(manifest)
  384          mutations = json.loads((HERE / 'mutants.json').read_text())
  385          record['inputs'] = hashes(input_paths(manifest))
  386          record['seed_revision'] = manifest['seed_revision']
  387          verify_reference(record, cases)
  388          resources = resource_cases(record)
  389          require(not {case['name'] for case in cases}.intersection(case['name'] for case in resources),
  390                  'Resource case names overlap the original manifest')
  391          record['tools'] = {}
  392          for tool in ('bun', 'node', 'python3'):
  393              record['tools'][tool] = successful(run([tool, '--version']))['stdout'].strip()
  394          require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
  395          for proof in ('src/descent-PROOF.bend', 'src/recursion-PROOF.bend'):
  396              item = {'file': proof, 'result': run([*SEED, ROOT / proof])}
  397              record['proofs'].append(item)
  398              line(item['result'], 'All terms check.')
  399          lanes = build_lanes(record)
  400          fixtures(record, manifest, cases, lanes)
  401          # A short harness limit prevents an expansion regression from running unchecked.
  402          # A timeout fails this gate; it is never a matched language diagnostic.
  403          fixtures(record, {'fixtures': resources}, resources, lanes, target='resources', timeout=2)
  404          bounds(record)
  405          mutants(record, cases, mutations)
  406          validate_manifest(manifest)
  407          require(hashes(input_paths(manifest)) == record['inputs'], 'Inputs changed during gate')
  408          record['inputs_unchanged'] = True
  409          record['counts'] = counts(record)
  410          record['status'] = 'passed'
  411      except Exception as error:
  412          record['status'] = 'failed'
  413          record['failure'] = repr(error)
  414          raise
  415      finally:
  416          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  417      total = record['counts']
  418      print(f"Descent gate passed: {total['seed_fixtures']} seed fixtures, "
  419            f"{total['accepted_books']} accepted books, {total['phase_observations']} phase observations; "
  420            f"{total['evaluation_values']} evaluator values, {total['wasm_values']} Wasm values; "
  421            f"{total['resource_seed_fixtures']} resource fixtures / {total['resource_phase_observations']} phases; "
  422            f"{total['bounds_observations']} bounds observations; "
  423            f"{total['mutants']} mutants / {total['semantic_kills']} semantic kills")

diff --git a/tests/compiler-nest/check.py b/tests/compiler-nest/check.py
index c4c9f504..3bedf283 100644
--- a/tests/compiler-nest/check.py
+++ b/tests/compiler-nest/check.py
@@ -18,6 +18,6 @@ SEED = ['bun', ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
 HOST = ROOT / 'scripts/run-wasm.mjs'
 FIELDS = '--profile=knot-fields-wasm-1'
-# Explicitly authorized conservative outcomes; these NEVER count as conformance.
-UNMET = {'rec-swapped-args', 'rec-alias'}
+# Historical overrides are retired; all 40 frozen outcomes must now conform.
+UNMET = set()
 
 

@@ -341,5 +345,5 @@ def main():
             'mutants': len(record['mutants']), 'semantic_kills': sum(len(c['lanes']) for c in record['mutants'])}
         record['qualification'] = {'complete': not record['unmet'],
-            'limits': 'The gate monitors two authorized conservative recursion outcomes; neither is counted as frozen conformance.'}
+            'limits': 'All frozen outcomes are required; source/backend/resource limits remain as specified.'}
         record['status'] = 'passed'
     except Exception as error:

diff --git a/tests/compiler-recursion/check.py b/tests/compiler-recursion/check.py
index 6b1d9a7b..e615e2ba 100644
--- a/tests/compiler-recursion/check.py
+++ b/tests/compiler-recursion/check.py
@@ -64,15 +64,41 @@ def reference(manifest):
 
 
+def revise(manifest):
+    """Keep the original freeze intact; migrate only independently refrozen outcomes."""
+    contract = ROOT / 'tests/compiler-descent/expectations.json'
+    reference = ROOT / 'tests/compiler-descent/receipts/reference.json'
+    frozen = json.loads(reference.read_text())
+    require(digest(contract) == frozen['inputs'][str(contract.relative_to(ROOT))],
+            'Descent expectations differ from the independent seed freeze')
+    expected = {c['name'].removeprefix('recursion/'): c for c in
+                json.loads(contract.read_text())['legacy'] if c['name'].startswith('recursion/')}
+    revisions = json.loads((HERE / 'expectation-revisions.json').read_text())['cases']
+    require(len({c['name'] for c in revisions}) == len(revisions), 'Duplicate expectation revision')
+    cases = {c['name']: c for c in manifest['cases']}
+    for revision in revisions:
+        name = revision['name']
+        require(name in expected and name in cases, ('unfrozen revision', name))
+        require(all(cases[name][phase]['exit'] == 3 for phase in ('check', 'eval', 'compile')),
+                ('revision must replace the historical conservative outcome', name))
+        required = {phase: expected[name][phase] for phase in ('check', 'eval', 'compile')}
+        # This original gate invokes the enum compiler, which still refuses fields.
+        if required['compile']['exit'] == 0:
+            required['compile'] = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\tconstructor-fields\t'}
+        require(revision == {'name': name, **required}, ('revision differs from frozen decision', name))
+        cases[name].update(required)
+
+
 # These replacements must remain uniquely located and independently typechecked.
 MUTANTS = [
     ('admit-any-self-call', 'check.bend',
-     'Bool.and(U32.is_eq(index,current),Bool.not(E.descends(items,smaller)))',
+     'Bool.and(live,U32.is_eq(index,current))',
      'False{}', 'same-parameter', 0),
     ('stop-propagating-fields', 'patterns.bend',
-     'E.descendants(level,E.levels(introduced),smaller)',
-     'smaller', 'direct', 3),
-    ('stop-nested-propagation', 'scope.bend',
-     'Bool.or(U32.is_eq(level,0),contains(smaller,level))',
-     'U32.is_eq(level,0)', 'even', 3),
+     'E.replace(bindings,level,value(token,type_id,tag,params,args))',
+     'bindings', 'direct', 2),
+    ('stop-nested-propagation', 'descent.bend',
+     'U32.is_eq(id,level),u => value,u => known(tail,level)',
+     'Bool.and(U32.is_eq(id,level),U32.is_eq(level,0)),u => value,u => known(tail,level)',
+     'even', 2),
 ]
 
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.
