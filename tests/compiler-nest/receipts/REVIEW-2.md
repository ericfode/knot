# Nest review round 2

All seven confirmed findings are fixed within the recorded scope. The final
scratch run passed **19/19 registered gates**, exit 0. The fixed-seed comparison
agreed on all 3,000 programs. Original nest conformance remains **38/40**: the
two explicitly unmet recursion cases and both general lowering theorems remain
open. This increment is ready for coordinator review; it does not establish
self-hosting or a live Perch/style pass.

| Commit | Change |
|---|---|
| `194f1ba` | Merge main `3c25d9b`, retain its 17 gates, regenerate census |
| `ebdad25` | Freeze 29 copied reviewer repros and 49 pinned-seed calls before repairs |
| This commit | Repairs, new gate and fuzzer, checked helpers, current receipts and handoff |

The original fixtures, expectation files and seed script are byte-identical to
`57a0c01`. The review fixtures and their expectations are byte-identical to
`ebdad25`. Existing gate assertions are unchanged. The old default-dropping
mutant now targets the binary negative matrix because its n-ary injection site
no longer exists; its required wrong observation and rejecting assertion are
unchanged. Registration appends the new gate and required names. Only nest-owned
execution receipts are refreshed here; the coordinator owns shared receipts.

| Finding | Disposition and evidence |
|---|---|
| Unsound default and empty-remainder acceptance | **Fixed.** `Decision` splits positive specialization from a live, unrefined negative `Remainder`. Variable rows reach a checked leaf even when no constructors remain. All 10 default-region repros now have the seed's rejection category in native/Bun check, eval and both compile profiles. `flat-control-reuse` retains all seven seed results. Constant-refinement and skipped-empty-body mutants are killed. |
| Forbidden enum `unreachable` | **Fixed, option (a).** Empty cases emit `i32.const 0`. Every enum-profile nest module uses the unchanged compiler-wasm whitelist. All 25 frozen enum hashes match in two compiler lanes and both profiles: 100 checks. A type-correct, executable `unreachable` mutant fails the whitelist. No instruction-contract extension. |
| Partitioned quota rejects small matrices | **Fixed.** `Expansion{node,remaining}` threads one decreasing total counter through both children. `deep-13`, `tworow-13`, `wide-type-depth3` and `self-shape` pass seed/evaluator/Wasm comparisons. The old `matrix-work` expectation is unchanged: its 13 independent strict columns require `T(0)=1`, `T(n+1)=2+2*T(n)`, hence 24,574 matrix visits against 4,096. The partitioned-budget mutant is killed. |
| Ground witnesses named as general laws | **Fixed by the requested rename.** `irrefutable_lowering_witness` and `exhaustive_matrix_witness` keep their checked equations. Both general theorems are explicitly unmet in CONTRACT and campaign state. The complete matrix proof entry passes all 21 matrix laws and its inherited chain. |
| Referenceable `_` | **Fixed.** Source lookup rejects exact `_` as `Invalid check free-name`; internal field identities still support reconstruction. Row, field and multi-column repros reject. Ignore and `_x` controls succeed. The anonymous-reference mutant is killed. |
| Comma-separated columns reported Invalid | **Fixed.** Both scrutinees and row patterns accept comma separators. C1/C2/C3/C5 and comma-patterns each match all five frozen seed calls; malformed C4 remains Invalid. A checked parser law covers comma scrutinees. The parser mutant is killed. |
| Variable match on a let binder reported Invalid | **Fixed.** An all-variable column aliases the latest let binder without inspection. `let-var-match` agrees on five seed calls in evaluator and Wasm, in both compiler lanes. The let-column mutant is killed. |

`review.py` registers `nest-review` alongside the original `nest` gate. Its
29 fixtures comprise 15 accepted and 14 invalid programs. Seven new semantic
mutants typecheck before execution and die in both compiler lanes (14 kills):
`refine-default-to-constant`, `skip-empty-default-body`,
`reference-anonymous-binder`, `partition-expansion-budget`,
`reject-comma-scrutinees`, `reject-variable-let-column`, and
`empty-unreachable`. Type errors and host failures do not count as kills.
Every rejected compile preserves an existing artifact.

The committed fuzzer uses seed **1313166164** and exactly **3,000** programs.
It covers ordered flag/multi-column/fielded/nested matrices, quantities,
aliases and ill-formed bodies. The pinned seed independently classifies each
program. Seed and native Knot both report **426 Accepted, 2,574 Invalid**;
Unsupported, Exhausted, host/internal failures, false acceptance and false
Invalid all have count **0**. All **426** accepted evaluator values agree.
This randomized control uses the native lane; the frozen regressions separately
cover both compiler lanes and Wasm. Fuzzing is bounded evidence, not a proof.
The generator and observation hashes are in [review.json](review.json).

Fresh gate execution: `BEND_NO_TELEMETRY=1 npm run -s gates`, scratch run
`run-hwr43bo5`, started `2026-09-28T02:52:52.694814+00:00`, measured wall time
374.911123 seconds, exit 0. The following counts come from that run's receipts
and completion lines. Counts describe different observation categories and
must not be summed as unique tests.

| Gate | Result and exact coverage |
|---|---|
| `frontend` | PASS: 14 reference fixtures, 28 parser observations, 24 boundaries, 4 original mutants; 29 classification fixtures in 2 lanes, 7 classification mutants, 174 downstream observations |
| `checker` | PASS: 49 fixtures, 98 checked observations, 10 depth observations, 16 catalog-bound observations, 7 mutants |
| `structural` | PASS: 16 fixtures, 64 phase observations, 4 boundary pairs, 7 mutants |
| `fields` | PASS: 40 fixtures, 240 phase observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants |
| `wasm` | PASS: 25 programs, 90 reference calls in 2 lanes, 62 rejection pairs, 44 boundaries, 7 mutants |
| `wasm-trust` | PASS: 3 entries, 0 proof holes |
| `fields-trust` | PASS: 4 entries, 0 proof holes |
| `structural-trust` | PASS: 2 entries, 0 proof holes |
| `owned-store` | PASS: 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| `flat-store` | PASS in each of 2 lanes: 13,621 observations, 3,534 instances, 2 installed-boundary states, 7 lifecycle checks; 9 mutants |
| `recursion` | PASS: 19 fixtures, 114 phase observations, 4 fuel probes, 3 mutants |
| `fields-wasm` | PASS: 8 fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 enum hashes, 30 boundaries, 4 mutants killed in both lanes, 5 checked laws |
| `census` | PASS: 33 compiler files, 549 declarations, 41 feature classes; generated inventory current |
| `perch-context` | PASS: 33 controls, 8 mutants, 19 compositions, 549 distinct declarations, 2 byte-identical preflights; role-limited 475 to 0, 0 blockers, 0 provider requests |
| `lint:verify` | PASS: 168 tests, 8 law rules |
| `bootstrap` | Harness PASS: 698 corpus files, 8 stages, 2 reached, 9 judge mutants, 4 controls; reference 698/698 and C1 56/56 agree |
| `classification` | PASS: 17 frozen seed outputs, 17 parser observations, 6 mutants, 16 filled frontend laws |
| `nest` | PASS within stated scope: 40 seed fixtures, 174 seed calls, 38 matching outcomes, 2 unmet, 76 check observations, 12 unmet phase observations, 25 accepted books, 386 evaluator and 386 Wasm values, 78 rejection phase observations, 24 boundaries, 100 enum hashes, 6 mutants / 12 kills |
| `nest-review` | PASS: 29 seed fixtures, 49 seed calls, 58 check observations, 15 accepted books, 98 evaluator and 98 Wasm values, 112 rejection phase observations, 7 mutants / 14 kills; 3,000 fuzz classifications and 426 evaluator values |

`npm run -s gates:verify` passes **18 tests**, including the six executable
runner semantic mutants. The complete `src/matrix-PROOF.bend` prints
`All terms check.` and includes the parser proof chain. No proof hole, axiom or
unsafe declaration was added. See [LAW_REVIEW.md](LAW_REVIEW.md) for quantified
helpers, witnesses and the two unproved general obligations.

The first full scratch run is retained as failed evidence: frontend and fields
mutant text anchors became non-unique in added code, and the enlarged manifest
groups exceeded the unchanged 48 KB context limit. Fields-trust was blocked by
its producer. Renaming only the added continuations restored the original
mutation anchors; bounded `interfaces-v1` selected-file groups restored complete
declaration coverage without changing assertions or limits. The final run above
passed all affected gates. Shared receipt drift in that run is **63 identical,
7 volatile-only, 16 semantic**, retained in the runner summary; it is not silently
accepted as a receipt refresh.

Offline Perch preflight has two distinct views:

- Required changed-files invocation: 11 Bend files, 289 declarations,
  **37 structural blockers** (36 truncated contexts plus unavailable composition),
  59 declarations with insufficient supporting-role context, exit 3. The combined
  composition is 143,009 bytes against 48,000 and has 78 nonlocal-import references.
  Truncation reasons: 7 caller/byte, 8 file-limit, 21 helper-limit contexts.
- Current manifest with `interfaces-v1`: 19 bounded groups, 33 files,
  1,021 group/declaration observations covering 549 distinct declarations,
  19 available compositions, 0 truncations, 0 role limitations, 0 blockers,
  exit 0. Checking is 33,538 bytes, matrix 34,788, matrix laws 30,812.

Both use **0 provider requests**. Compression, Delight, Memetic identity,
Anticipation and Payoff are **unrated**. The bounded manifest resolves structural
review packaging; it does not replace the disclosed changed-files blockers or
establish model approval. Live semantic/style review belongs to the coordinator.

Remaining work is explicit. `rec-swapped-args` and `rec-alias` still report
Unsupported against unchanged Invalid expectations; `descent-2` owns their
decreasing-call rule. A new source match on a residual binding reports
`Unsupported check default-scrutinee`; carrying arbitrary narrowed constructor
sets through those source matches is future work. Only the latest let binder is
accepted for the new variable-column alias path. The two general lowering laws
remain unmet. Bootstrap compile/A2 are blocked by `Unsupported lex literal`;
later stages are not run. Structured host arguments, generic/closure patterns,
owned-memory reclamation and full self-hosting remain outside this acceptance.

Evidence: [nest.json](nest.json), [review.json](review.json),
[verification and hashes](review-verification.json),
[normalized full runner summary](review-all-gates.json.gz),
[changed-files preflight](review-preflight.json),
[bounded manifest preflight](review-manifest-preflight.json.gz).
