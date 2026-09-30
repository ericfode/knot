# Closure mechanism review

The contract is fixed by the original 42 fixtures and 292 seed calls in
`expectations.json`, plus the expectation-first `probes.json` and
`regressions.json` commits. The original fixtures, observations and regeneration
script are unchanged. `SPEC.md` bounds this review; `src/SPEC.md` defines the
accepted capability and host preconditions.

The reading hypothesis is one code/environment representation for all function
values. Checking records an arrow identity, a lambda site and free-variable
descriptors. Named values and partial calls use the same representation. The
independent evaluator stores environments directly. Wasm turns each arrow into
an ordinary constructor family and one apply dispatcher, retaining the existing
cell representation. Site identity, dense runtime tags and lexical levels have
different roles and remain explicit.

The three complete proof entries are `src/closure-types-PROOF.bend`,
`src/closure-check-PROOF.bend` and `src/closure-PROOF.bend`. They fill 24 laws:
six type equations, twelve checking/evaluator equations and six lowering
equations. All nine root `src/` proof entry points also check. The gate receipt
records exact commands, source hashes, proof results and the declared law names.

| Obligation | Checked equations | Independent witness |
| --- | --- | --- |
| Arrows have stable identity and kind Type | `arrow_kind`, `signature_end`, `signature_step`, `interned_arrow_is_stable` | Arrow fields, nested/returned closures, invalid reusable closures and Data fields |
| Affine capture usage transfers at closure construction | `affine_capture_is_transferred`, `affine_capture_cannot_be_consumed_twice` | Frozen affine-capture rejections; duplication mutant |
| Erased reads retain checking without live consumption or storage | `erased_argument_has_no_live_read`, `erased_read_has_no_live_capture`, `erased_capture_skips_lookup` | Frozen erased captures, nested-erasure regression, exact 8,192-cell arena boundary; stored-live mutant |
| Discarded binders cannot be read as local variables | `discard_is_not_a_reference` | `_ => _` rejects; `_ => On{}` accepts; a discarded binder leaves global `_()` visible |
| Closure expressions are computed scrutinees | `closure_application_is_a_computed_scrutinee`, `lambda_is_a_computed_scrutinee` | Two seed-rejected scrutinee regressions retain source rejection rather than InternalFailure |
| Closing starts an explicit captured environment | `close_starts_with_an_empty_environment` | Returned closures, nested captures and reconstructed-parent regression; dropped-capture mutant |
| Applying a closure evaluates callee then argument and enters its body | `apply_evaluates_the_function_first`, `apply_closure_retains_its_environment`, `apply_enters_the_body_without_a_return_frame` | All agreeing seed/evaluator/Wasm calls, including partial application and CPS |
| Lowering preserves capture order and quantities | `capture_arity`, `capture_quantity`, `close_has_one_cell` | Multiple captures and sites; exact erased-layout boundary |
| Each invocation calls the dispatcher for its arrow | `invoke_has_one_dispatch`, `outer_levels_are_unchanged` | Frozen `defunc-sites`; wrong-dispatch mutant |
| Resource failure remains explicit | `no_type_budget`, `rewrite_exhaustion` | Evaluator fuel, emitter depth, output capacity and arena exhaustion probes |

`arrow_location` preserves the original domain span. The capture-length law is
structural induction; the remaining equations are local reductions with
quantified arguments or fixed lexical witnesses. They contain no hole, axiom,
unsafe inhabitant or contradictory assumption. They are not a universal theorem
of checker soundness, defunctionalization correctness or memory refinement.
Corpus agreement is a separate finite observation, not a proof by renaming it.

The general capture/application preservation obligation is open under D21 and
recorded in `src/SPEC.md`'s trust inventory. It relates independent evaluation
of a source-constructible closure in any checked monomorphic book to execution
of its lowered constructor/apply dispatcher, within both resource bounds.
The original 24 laws and their domains are unchanged. The 32 new refresh edges
add independent two-seed-lane observations; they do not close the obligation.

Each of the five source mutants must typecheck before it builds and executes in
both compiler lanes. A kill must be the intended wrong enum value, wrong affine
acceptance, wrong allocation boundary or deep call-stack exhaustion after a
working shallow control. Crashes, unrelated diagnostics and timeouts cannot
count as semantic kills. The 2,048-continuation probe is bounded tail-call
evidence; the unchanged arena has no reclamation or unbounded-space guarantee.

Adversarial reading found two missing scrutinee cases and two discard/name
resolution defects. Their seed observations were committed before repair, with
accepted controls for capture erasure, reconstruction, partial application and
empty application. Matching inside lambdas remains restricted by the seed's
binder rules; generic, dependent and erased-remaining-parameter forms retain
explicit Unsupported boundaries. The generic chooser fixture still requires
agreement and retains 19 blocked calls. It is not counted as passing.

Only the separately committed structural/function-field catalog pin changes.
The enum-profile byte comparisons and all earlier gate assertions remain
independent. Function values cannot cross the host boundary; an empty dispatcher
is unreachable for source-constructible values under the enum-only host
precondition. This is not a guarantee for forged function handles.

The existing fields gate caught extra checker-depth consumption introduced by
the curried-call route. Exact-arity named calls retain the original direct
argument-checking path. Its fixed acceptance depths 5, 6 and 14, together with
the immediately lower exhausting depths, remain independent regression gates.

Offline preflight records no model ratings or semantic review. See
`receipts/preflight-selection.json` for all changed Bend targets and intentional
negative-parser exclusions, and `receipts/preflight.json` for context limits.
Live Perch source and law-packet review belongs to the coordinator. None of the
five style axes or the bounded composition is reported as qualified here.
