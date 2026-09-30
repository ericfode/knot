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
Disposition: retain the verbatim extraction subject to the unchanged deterministic
suite; live review and remaining context fitting belong to the coordinator.

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

At the source checkpoint, full-suite acceptance and receipt promotion are pending.
The final acceptance section will record one complete run, every gate's exact
counts, matching current-input hashes and the unchanged frozen inputs.
