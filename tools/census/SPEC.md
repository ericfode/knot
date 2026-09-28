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
