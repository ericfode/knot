# Descent rule review

The public behavior is fixed in `SPEC.md` and `cases.json`. This packet covers
`scope.descendants`, `scope.descends`, `patterns.finish/open_fields`, and
`check.callable/call_result/call_body`. The complete proof entry is
`src/recursion-PROOF.bend`; its 16 new laws are filled. It also imports the
previous frontend, checker, runtime, catalog and field proofs (34 laws).

The reading hypothesis is one monotone set of strict descendant lexical levels.
It separates provenance from the ordered match frontier, so ordinary field
binding, nested matches, shadowing and calls share the same criterion. Checked
term shape supplies the second half: only a Reference carries that provenance
into a self-call. Reconstruction and computation cannot reuse the mark.

| Obligation | Law or proof boundary | Independent witness / mutant |
| --- | --- | --- |
| Parameter-0 fields enter the descendant set | `root_fields_are_smaller`, `opening_root_records_descent` | `direct`; stop-propagating-fields |
| Descendant fields also enter it | `descendant_fields_are_smaller`, `opening_descendant_records_descent` | `even`; stop-nested-propagation |
| Other parameters confer no descent | `unrelated_fields_stay_unmarked` | `other-parameter`, paired with `first-parameter` |
| First Reference must be marked | `marked_reference_descends`, `root_reference_does_not_descend`, `later_argument_cannot_establish_descent`, `empty_call_does_not_descend` | `same-parameter`, `second-descent`; admit-any-self-call |
| Reconstruction and calls are not References | `rebuilt_argument_does_not_descend`, `computed_argument_does_not_descend` | `rebuilt-parent`, `rebuilt-constructor`, `computed`, paired with `direct` |
| Fresh lets do not inherit provenance | `local_binding_preserves_descent` | `shadow-let` / `after-let`, plus `shadow-field` |
| Descending calls retain arguments, result and usage | `descending_self_call_is_checked` | even/add/mirror/length seed ⇔ native evaluator ⇔ Bun evaluator |
| Missing descent stays Unsupported, including erased context | `nondecreasing_self_call_is_unsupported` | seven Unsupported fixture outcomes, both CLI lanes |
| Earlier calls need no descent; later live calls remain invalid | `earlier_call_needs_no_descent`; unchanged declaration-order rule | `ordered-calls` / `mutual`, existing forward/erased-forward corpus |
| Fuel exhaustion is a runtime outcome | `recursive_evaluation_exhaustion` | `deep` / `deep-input` at 600 transitions, both lanes |

These are helper/boundary equations, including fixed lexical-level witnesses
with quantified tokens, arguments or environments. They are not an induction
proof of checker soundness or termination of every accepted book. The populated
fixture scopes exercise actual parameter binding, field opening, checking and
evaluation; no impossible antecedent, axiom, unsafe inhabitant or hole establishes
the new claims. The source-to-machine relation remains validated by differential
observations rather than a universal refinement proof.

Adversarial reading checked that the first parameter itself never enters the
set, a later parameter's field cannot enter it, lexical shadowing allocates a
new identity, and reconstruction changes the checked term away from Reference.
Matching a descendant preserves old marks and adds only newly allocated field
levels. Branches receive immutable scopes, so marks do not escape into sibling
arms. Existing quantity and order gates still run before a book is exposed.
All 1,534 old command observations and all 25 Wasm binaries remain unchanged.

The three mutants alter type-correct implementation code and produce exactly
the wrong acceptance/capability outcomes described in the README. The fixed
seed receipt predates implementation, and the gate refuses fixture/expectation
hash drift. The reference's later-parameter descent case deliberately remains
Unsupported in Knot. Host timeouts and internal errors cannot satisfy the new
gate's expected source or fuel outcomes.

Source hashes and exact commands are in `receipts/recursion.json`; the
preimplementation hashes are in `receipts/reference.json`. Perch preflight is
offline and supplies no semantic or style rating. The seven selected mechanism
declarations fit the review context; complete-file context blockers remain
explicit in `receipts/preflight.json`. There is no recursive Wasm execution,
owning-heap proof or performance evidence in this increment.
