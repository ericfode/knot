# Baseslice executor precheck repairs

Starting head: `264b9104535995fccd649917009c2c256d3d31c5`.
The plan and BS1 acceptance in [REPORT.md](REPORT.md) remain historical evidence.
This round addresses C4 `999529c399e242428e16` and C5 `c6c631fc187e93673c54`.
Both findings are confirmed; neither is disputed.

## C5: split checked-term assembly from book resolution

Reading hypothesis: argument lists, lets and branches share one small algebra
of external affine uses. Reading those five operations together makes the
sequential/disjoint and alternative/union rules visible without tracing catalog
construction or the recursive resolution dispatcher.

`src/checked-terms.bend` contains `prepend_argument`, `let_result`, `prepend_arm`,
`case_result` and `checked_function`, moved verbatim from the starting checker.
Only their seven call sites gain a module qualifier. No signature, branch,
diagnostic, quantity, budget or accepted language changes. All eight existing
mutation anchors in `src/check.bend` remain unique. Frozen suites and expectations
are unchanged. Census records the module move: 31 files, 432 declarations,
40 classes; no declaration or feature class is added.

The manifest's `checking` group now names the complete checked-term assembly
family and its closed syntax/core/scope imports. The catalog and field-scope
families retain their existing groups. `src/check.bend` remains reviewed in
`wasm-emission`, `driver-pipeline`, `checker-laws` and their proof families; each
gets the new helper module so no local import is omitted. The former whole-book
group shrinks for this explicit source seam, not to claim a whole-checker pass.
Those larger compositions were already unavailable and remain so.

| Offline observation | Before | After |
|---|---:|---:|
| checking composition bytes / 48,000 | 50,041 | 14,640 |
| checking composition available | no | yes |
| checking unresolved composition references | 0 | 0 |
| checking declarations / truncated contexts | 141 / 23 | 64 / 13 |
| full manifest groups / unique files | 17 / 30 | 17 / 31 |
| full manifest declarations / truncated contexts | 2,497 / 376 | 2,420 / 366 |
| full manifest available compositions | 8 | 9 |
| provider requests | 0 | 0 |

These are structural observations, not ratings. Conceptual compression, Delight,
memetic identity, Anticipation and Payoff remain **unrated**: no distributions or
automatic style pass. The fixed role-scaled targets and all rubrics are unchanged.
The two changed files' separate preflight reports 37 declarations, 6 truncated
contexts and a 50,327-byte full collaborator closure. This remaining whole-checker
limit is explicit; the source split qualifies only the bounded assembly family.
Disposition: retain the verbatim extraction with the unchanged deterministic
suite passing; live review and remaining context fitting belong to the coordinator.

Initial validation: seed `src/check-cli.bend --check-only` passes; the existing
manifest tests pass 20/20, including complete local-import closure and offline
operation. Census generation and `census:check` pass. Raw before/after preflights,
seed output and TAP are in ignored `.local/baseslice/precheck/`.

## C4: regenerate current evidence after the final source edit

The six stale inputs belong to a gate output that predates the review repairs.
Regenerate `base-enum` through the unchanged runner; promote only baseslice-owned
normalized evidence. Do not rewrite any baseline, frozen oracle or expectation.
Shared receipts are regenerated in the isolated gate export and remain the
coordinator's merge-time refresh responsibility.

The unchanged gate regenerates the current-input sections after the final source
edit. Every recorded current input matches; baseline and freeze sections stay
unchanged. Full-suite acceptance and receipt promotion are complete below.

## Final acceptance

Source checkpoint: `fd0020182b5177424bb66dc7f704f1235dc5b15f`. `npm run -s gates -- --jobs=1` passes **15/15**, exit **0**, in **443.69945 measured wall seconds**. The Xcode PATH/SDKROOT selection is the same as the preceding review; no toolchain bytes, flags, frozen harnesses or budgets change.

| Gate | Status / exit | Exact counts |
|---|---|---|
| frontend | PASS / 0 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | PASS / 0 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | PASS / 0 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | PASS / 0 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | PASS / 0 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | PASS / 0 | `{"entries":3,"proof_holes":0}` |
| fields-trust | PASS / 0 | `{"entries":4,"proof_holes":0}` |
| structural-trust | PASS / 0 | `{"entries":2,"proof_holes":0}` |
| owned-store | PASS / 0 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | PASS / 0 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | PASS / 0 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | PASS / 0 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | PASS / 0 | `{"classes":40,"declarations":432,"files":31}` |
| lint:verify | PASS / 0 | `{"law_rules":8,"tests":127}` |
| base-enum | PASS / 0 | `{"agreed_books":2,"byte_identical_modules":2,"declarations":7,"deferred_books":1,"evaluator_observations":62,"execution_lanes":2,"fixtures":7,"laws":8,"mutants":5,"output_preservation_checks":10,"proof_holes":0,"reference_calls":31,"rejected_books":4,"review_agreed_books":13,"review_amendment_seed_witnesses":4,"review_byte_identical_modules":12,"review_evaluator_observations":26,"review_fixtures":27,"review_lane_observations":162,"review_laws":7,"review_mutants":3,"review_output_preservation_checks":30,"review_proof_holes":0,"review_rejected_books":10,"review_unsupported_books":4,"review_wasm_observations":24,"seed_calls":32,"seed_lane_observations":64,"wasm_observations":62}` |

[The current enum receipt](../enum/receipts/enum.json) records **82 current-input hashes**, including the new helper module; all match head. [The current suite receipt](receipts/gates.json) records **97 matching tested inputs**, all fifteen results and the unchanged thirteen frozen identities. It preserves the preceding passing run and all three earlier failed runs as history. The old BS1 suite receipt also retains its preceding run under `historical_passed_runs`; its standalone additional counts are historical. No baseline or frozen oracle is regenerated.

The plan remains **72 compiler-runtime / 110 static Base declarations**, partitioned **7 BS1 + 28 unmerged literals identities + 37 remaining runtime declarations**. This round completes the two executor findings and retains BS1 acceptance. Coordinator actions remain main integration, shared receipt refresh and live Perch/context fitting. BS2–BS8 wait on their named language/VM increments; no imported Base or self-hosting fixpoint is claimed.
