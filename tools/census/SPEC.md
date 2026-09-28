# Compiler census contract

This offline source inventory does not implement or validate Bend semantics.
It uses the vendored pinned parser, original declaration observers and resolved
local module identities. It never fetches dependencies or reads environment files.

The inventory covers every `src/*.bend` file, the runtime entry closures of the
six packages in `packages/releases.json` (including OutputBuilder's byte entry),
and pinned Base. Hash imports resolve to release-verified repository bytes, or
to the seed's existing local package cache if the working copy has evolved.
No fetch is attempted. Published and working-copy identities remain separate.
Proof entries in `src/` remain in the source
inventory; executable roots exclude them.

Feature classes have stable names and definitions. Per-declaration evidence
includes source spans, classes, static references and captures. Import classes
belong to files. Explicit type/proof dependencies are separate from executable
body dependencies. Law fills inherit the law's signature: bare fill names are
not quantity parameters. Unknown parser forms and unresolved modules fail closed.

Base closures start at `src/lex.tokenize` and `src/parse.parse`, and separately
at `src/compile-cli.main`. The JS/native runtime closure includes signatures and
constructor types, cutting operation bodies at the seed's `OPERATIONS`, foreign
definitions and word representations at `WORDS`. The value-reference slice
excludes signatures, annotations, rewrite evidence and statically erased
arguments. Template value arguments are retained, as is the seed's implicit
U32.to_nat dependency for large Nat literals. Both branches and callbacks remain.
These are static upper bounds, not executed traces or the seed optimizer's
emitted function set. Dynamic calls and template instantiation limits stay
explicit. A third, uncut syntactic closure includes types and proof bodies.

Accepted-profile evidence is derived from the existing fixed fixture manifests
and their gate programs. Keep parsing, catalog inspection, checking, evaluation
and Wasm execution distinct. A class is evidenced only by a fixture successful
at that stage. Failure records retain exact classifications and diagnostics;
their other features do not become unsupported by association. Missing evidence
is not a rejection. Gate executions are reported separately from this inventory.

`npm run census` regenerates committed JSON without timestamps or absolute paths.
`npm run census:check` also compares exact committed bytes. Neither command edits
the approval policy. New classes per declaration, new source files, and changed
imports require an explicit policy diff. Package dependency features are checked
transitively, including arrays behind Vec. Removal is allowed, but changes still
require regenerated manifests.

## Fixed expectations (literal review, before implementation)

- `control.bend`: two nullary constructors, identity, no lambda or import.
- `lambda.bend`: a higher-order parameter, variable call and an explicit identity
  lambda; the seed must accept it. Adding this shape to the control violates its
  feature approval, even though it is valid Bend.
- `features.bend`: generic quantity parameters, a captured variable, a variable
  call, structural recursion, multi-scrutinee/nested/wildcard patterns, each
  scalar literal kind, list literal, template and filled reflexive law.
- An unused newly added Base/package import violates import approval. Comments
  and string contents containing feature spellings do not manufacture features.
- With roots A -> B -> Base intrinsic, retain A, B and the intrinsic, but do not
  traverse the intrinsic's implementation. A local lookalike is not intrinsic.
- Erased/type references remain in static closure, but not execution closure.
- Invalid, Unsupported, Exhausted, HostFailure and InternalFailure stay distinct.
- Regeneration is byte-identical; source, fixture, gate or pin changes invalidate
  the committed manifests. Missing files and unsupported import forms are errors.

Tests also inject parseable JavaScript semantic mutations into the census:
drop lambda detection, ignore import approval, bypass the intrinsic cut, and
conflate Unsupported with Invalid. Unchanged observations must kill each.
No new Knot language capability is added, so seed/evaluator/Wasm differential
fixtures remain the existing corpus rather than a fabricated new execution gate.

## census-2 fixed expectations (literal review, before implementation)

Discover every gate in the literal `GATES` registry without executing its Python
module. Inspect its suite directory, plus every `tests/compiler-*` directory,
for fixture manifests. An explicit path-to-adapter table owns each format;
unknown directories, unknown formats and missing manifests are reported and
contribute no evidence. Companion manifests describe one suite, not duplicate
fixtures. Hash the registry, gate programs and every consumed manifest.

The existing five formats retain their stage boundaries. Recursion's `check`,
`eval` and `compile` outcomes are independent; compilation alone is not executed
Wasm. Fields-Wasm joins `cases` to frozen `observations`: `arena-overflow` is
Wasm Exhausted, and `deep-call` is evaluator Exhausted. Neither failure supplies
positive evidence for that stage. All other frozen successful calls do.

Reviewed branch formats: nest uses `fixtures[].knot` and `observed.calls`;
modules uses `fixtures[].knot.obligation`, `knot_expected` and `calls`; literals
uses `fixtures[].knot` or `knot_expected` and `calls`; generics, closures and baseslice use
`cases[].knot.require` joined to `observations.fixtures` by case name. Only
unconditional agreement supplies check/eval/Wasm evidence. `agree-or-unsupported`
and unpinned rejection remain alternatives, never a guessed outcome. Seed
success alone cannot override Knot's frozen Unsupported outcome. Nest's empty
call-domain control still has its frozen successful `observed.main` execution.
The modules fixture loader accepts reviewed bare-relative imports and reads hash
packages only from that suite's hash-verified local bundle, never a cache or hub.

`selfhost.json` measures the existing JS runtime/type closures rooted at
`src/compile-cli.main` and at `src/lex.tokenize`, `src/parse.parse`. Count unique
resolved declarations, including datatypes and transitive package/Base entries,
but exclude law/proof files. Filled laws in ordinary files can implement runtime
functions (for example Base String.cmp); retain those resolved identities and
merge their law/fill features instead of losing executable dependencies. Record the scope breakdown
and excluded identities. Keep intrinsic/foreign boundaries visible. A
declaration requires its own classes plus its file's import classes. Do not
propagate a callee's missing classes into its callers: each closure declaration
is measured separately. Check and Wasm counts each mean *all required classes
have at least one successful fixture at that stage*, not compiler acceptance.
Missing classes rank by descending blocked-declaration count, then class name;
per-declaration missing sets and all inventories sort deterministically.

Literal meter control: three executable declarations require respectively
`calls`, `calls + lambdas`, and `fields`. With check evidence for calls and
fields, and Wasm evidence only for calls, counts are 2/3 and 1/3. A fourth
declaration in `src/control-LAWS.bend` must never raise either denominator or
blocker count. An unknown suite containing a lambda fixture contributes nothing.
A failed lambda fixture likewise contributes nothing at the failed stage.

Small JSON controls freeze these adapters and meter observations. New semantic
mutants admit a failed fixture, admit an unknown suite, and count a law file.
`census --check` remains the registered gate; no new gate or source capability
is introduced. `census:meter` computes a read-only, one-screen summary; normal
census generation/checking owns the new manifest and verifies identical bytes.

## census-2 review round 2 expectations (literal review, before repair)

A recognized fixture format is not evidence of implemented Knot behavior. Each
adapter names its gate in `scripts/gates/run.py::GATES`; that exact gate must
invoke a program in the adapter's suite directory before its fixtures contribute
accepted evidence. A trust gate or another gate in the same directory does not
qualify the suite. A correctly named gate pointing elsewhere does not qualify it.

Recognized suites without that registration are frozen **requirements**. Retain
their fixtures, hashes and exact stage outcomes separately from accepted
fixtures. `selfhost.json.requirements` lists the ungated suites and, for every
feature class and stage, the successful frozen fixtures that would supply
evidence once their gate lands. Invalid, Unsupported, Exhausted, host/internal
failures and ambiguous alternatives supply neither positive evidence nor
positive requirement coverage at the failed stage. Unknown formats supply neither.

Keep the existing evidenced counts and missing-class rankings. Add a second
count: declarations covered by gated evidence **or** frozen requirements at
each stage. This inclusive count never falls merely because a gate lands; it
is planned class coverage, not implemented behavior. Retain its per-declaration
gaps and label both counts in the one-screen meter.

Literal controls reuse the already checked `lambda.bend` as an ungated closures
fixture. It provides no accepted lambda evidence until the mapped closures gate
is registered, including when only a trust gate shares its directory. The meter
control keeps 2/3 check and 1/3 Wasm evidenced; adding a frozen lambda requirement
covers 3/3 check and 2/3 Wasm, leaving the field's Wasm obligation unfilled.
Promoting that requirement to gated evidence preserves inclusive coverage. A
syntax-valid semantic mutant admitting ungated fixtures must fail the same
unchanged evidence assertions. Existing compiler assertions are unchanged.
