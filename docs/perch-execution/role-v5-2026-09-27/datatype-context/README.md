# Datatype context repair — 2026-09-27

This offline tooling increment fixes a confirmed resolution defect. It changes
no Bend source, rubric, role classifier, model, threshold, exclusion or numeric
context limit. It makes no provider requests and does not reassess old answers.

## Reproduction and scope

[before.json](before.json) reproduces the exact historical source, prepared-state
and context identities for `research/adaptive-tasks/task.bend::tick_owned`,
`task.bend::combine`, and `comparison-gate/oracle.bend::frame_json`.
The two task helpers already received local `Payload` source but also an
`unresolved-or-builtin` entry for it. The gate helper's explicit `F.Frame` import
was marked `declaration-not-in-import`, and its datatype source was omitted.
All three captured contexts had `truncated: false`. The resolver's declaration
map contained functions/laws but omitted the parser's separate datatype list.

Known Base references were already filtered by the existing role classifier;
this repair does not alter that catalog or infer new role/style judgments.
The source receipts named inside the capture stay historical.

The parser now records supplementary datatype/type-reference metadata from the
pinned parser AST, including imported aliases and generic type heads/arguments.
The existing function/law declaration and reference graph remains unchanged.
Context resolves local types and follows explicitly referenced imported types
transitively. Imported type helpers share the existing helper budget; cycles and
already admitted files at the exact cap are reused. Missing-declaration lookups
retain the inspected import's source identity. Source snapshots remain immutable.

Direct datatype style targets still use one file, four callers and 48 KB.
Required external imports therefore report explicit `context-file-limit` and
truncation. Composition only admits its explicitly selected file group within
48 KB. Remote imports, missing declarations, omitted capped context and parser
failures remain unavailable; this is not whole-project dependency completeness,
constructor-call resolution, type checking or proof acceptance.
The standalone parser still rejects imported `+` type syntax when it requires
unavailable quantity/arity context; this metadata repair does not load compiler
dependencies to change that boundary.

## Identities and cache controls

[after.json](after.json) records the same three Bend source hashes with new
context/state/request hashes. Both captures contain complete prepared requests
and source provenance; [capture.mjs](capture.mjs) exclusively creates a named
capture and never calls a provider or overwrites evidence.

The parser profile changes from `bend-2.0.29-574b6d3-observer-v2` to
`bend-2.0.29-574b6d3-observer-v3`; context carries
`working-tree-datatypes-v1`. The installed adapter is
`language-pack-1.20-v3+knot-bend-a91631dcc912aed6`.

[cache-invalidation.json](cache-invalidation.json) records the exact before/after
identities and code hashes. [check-cache.mjs](check-cache.mjs) uses a temporary
answer cache with offline probe values: all three old identities hit, while all
six probes using the new parser/context identity or changed request miss. It
removes only its temporary cache and never touches existing answers.

## Validation

- [regression-before.txt.gz](regression-before.txt.gz): three of four new controls fail
  against the original implementation; the existing missing-import behavior
  passes.
- [regression-after-1.txt](regression-after-1.txt): all four pass.
- [regression-after-2.txt.gz](regression-after-2.txt.gz): one added snapshot assertion
  fails because the test rerun omitted its original explicit limits. This test
  harness error is preserved; no implementation or acceptance rule was changed
  to address it.
- [regression-after-3.txt](regression-after-3.txt): all five pass after restoring
  the same limits in the snapshot control.
- [focused-tests-1.txt](focused-tests-1.txt): 73/73 pass across parser, integration,
  style, potential and role suites, including the sixth direct-datatype and
  composition control.
- [lint-verify.txt](lint-verify.txt): `npm run lint:verify` completes once with
  91/91 tests (the prior 85 plus six new tests) and eight law-rule wiring checks.
  No provider contacted. `git diff --check` also passes.

The six additions exercise local/imported/aliased datatypes, generic AST spans,
transitive cycles, exact-cap reuse, missing files/declarations, malformed
dependencies, file/helper/byte limits, negative-lookup provenance, snapshot
immutability, unchanged graph references and direct datatype/composition limits.
Fresh review is required for new style judgments; these receipts establish
context preparation and cache invalidation only.
