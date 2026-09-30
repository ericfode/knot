# Nest precheck dispositions — round 14

Source checkpoint: `486ae5ff`, after `65dc4276` (seed freeze), `3dea55a1`
(frozen-path restoration), `2c915e1a` (portable historical receipts) and
`bb8e11a9` (standalone parser event audit).
This report extends [REVIEW-13](REVIEW-13.md); its completed round-13 work is retained.

## C1: constructor patterns and recognized prefixes

Fixed `1dbcbb94227bdcc882ce`: the exact probe SHA
`208934010de44d636bfb175c0baea8e9bfe320269862593dab1c0b06e2cd86e0`
now reports `Invalid check unknown-constructor` before `Parsed`. The seed
rejects its `On{}` pattern at offset 71 because that constructor is declared
later. `parse.events` reuses `catalog.pattern_constructor` and its source-event
comparison. Nested patterns, nested matches and discarded rows are traversed;
constructor expressions retain forward references. The check-phase vocabulary
is preserved, so none of the existing frozen outcomes moves.

[precheck-expectations.json](../precheck-expectations.json) fixes ten sources
before the repair: all seven exact supplied hashes, the same forward pattern
in a discarded row (seed offset 87), an earlier-declaration control and a
forward-expression control. Both accepted controls have literal `main = On{}`.
[precheck.py](../precheck.py) replays seed parse/check observations, then parsing,
checking, evaluation and both emitters in native and Bun lanes. It observes
100 phases, 32 preserved rejected artifacts, four evaluator values and eight
executed Wasm values. All three type-correct mutants are killed in both lanes:
bypass the public audit, ignore declaration order, and treat an expression as
a pattern. Three new filled frontend laws cover the event witnesses and the
expression distinction; they are not a general parser soundness theorem.

The first full run exposed a masked checker mutant in `nest-round11`:
`parse.events` rejected `dead-single-unknown` before the unchanged
`audit-skips-bodies` mutant could exercise the matrix checker. `486ae5ff`
keeps the event audit at the standalone parser boundary. Check, evaluation
and compile paths run `parse.run` in `Book` mode, then the comprehensive
whole-book checker; no continuation receives unchecked core. The checker
applies the same catalog event rule with arity, types and quantities.
No fixture, expectation, negative assertion or mutant is changed. A targeted
replay of all three body/nested/let audit mutants first type-checks them and
then records six semantic kills across the native and Bun lanes in
[precheck-audit-isolation.json](precheck-audit-isolation.json). The failed
snapshot's logs are retained; it was stopped before a fresh full run.

Disputed under the binding vocabulary ruling: `c4718118b8d452bda6f2`,
`88f22e213803d6b8a72c`, `4039b32a911728e7ffe7`, `8e0d007bc620719d28fd`,
`99a5fb62700af98c920a`. Each exact dead-minus source is refused as
`Unsupported parse operator` in every phase. The fresh seed reason at offset
101 is `a type for this operator (write (a - b : Nat))`. The coordinator's
standing ruling in COORDINATOR-STATE.md and nest-fix9.md explicitly requires
Unsupported for continuing operator sugar: an annotation requirement is not
a syntax claim Knot makes. C1.premature treats coincident offsets as proof
of a syntactic defect without inspecting that reason. No source is accepted,
evaluated or emitted; the parser stops at the recognized prefix. The existing SPEC prefix table
lists `operator`. Marker-gap Invalid behavior and its frozen controls remain
unchanged.

Disputed under the explicit scope restriction: `3e7f002746acdd34676c`.
The exact dotted probe's seed rejection at offset 90 reproduces. Every Knot
phase refuses it as `Unsupported parse dotted-binder`; no artifact changes.
The standing dotted-binder ruling requires that stopgap until modules installs
the scope-aware rule, and nest-fix9.md says it is not this executor's repair.
SPEC now lists that recognized prefix in its table. Its suffix is not checked.

## C3: frozen files, capability pins and census

Fixed `9f4eb2b7cc6cd456f266` and `24d9a4ea7e06181d0715`: campaign state and
`tests/perch-context/check.py` are byte-identical to effective base `25b3a5b6`.
The proposed state survives only in ignored `.local/nest/` and the owned reports.
The timeout-only foreign edit is removed. Fixed `d3e86d151d9593edc447`:
the regenerated census and its check pass; the source commit contains the
complete printed per-declaration approval summary.

The inherited capability-pin conditions are disputed as requests to revert
seed-confirmed, required matrix behavior. They are preserved byte-for-byte
from the starting head `6ed16719`; this session amends no existing pin.
Fresh seed runs reproduce all four values below. Each original freeze preceded
matrix implementation `57a0c01d`:

| Condition | Frozen row | Seed value | Original freeze |
| --- | --- | --- | --- |
| `1edc1d233d5f8396faf7` | checker duplicate-arm | `On{}` | `f5bcc0ca` |
| `5a5e0e99a8cad16b2cab` | fields nested-pattern | `Off{}` | `4b024ee2` |
| same | fields nested-single-pattern | `On{}` | `2810a178` |
| `c8797540d2c0063c7234` | classification multi-scrutinee match | `On{}` | `e82c79c1` |

`0e4cf4252a837aa62567` is the inherited frontend harness adaptation that
executes the accepted classification row. It retains exact parser/evaluator
values, checks actual Wasm execution, retains every negative diagnostic and
artifact-preservation assertion, and re-expresses the match mutant as rejection
of the newly accepted form. The current frontend and classification gates pass
with those assertions. Restoring that harness alone leaves an accepted row
without its downstream checks and restores a removed mutation anchor; restoring
the row too contradicts the requested multi-scrutinee capability and the seed.
These exceptions need explicit coordinator bookkeeping/ratification if the
precheck manifest lacks their earlier authorization. A commit-message claim
alone is not authority; no authorization file is changed here.

## C4: portable history and current evidence

The 25 reported host-path receipts are fixed by
[portable.py](../portable.py), reusing the gate path normalizer and `$GATE_RUN`.
An independent comparison verifies 32,585 path-string replacements with
identical shapes, array order, numeric values and booleans, zero host paths
and idempotence. Historical source hashes and observations are preserved.
This is a path-only normalization, not a refresh or a new execution claim.

The precheck still reports stale input hashes in thirteen earlier nest receipts,
including the now-historical round13.json. That is acknowledged history, not
current-tip evidence. The prompt delegates existing-gate/shared refresh to the
coordinator; nest-r12.md and this directory's README likewise require it after
merge. Those artifacts are neither rehashed nor relabeled to claim fresh
execution. Current evidence is the fresh runner snapshot and the new
precheck gate receipt. The source-level parser fix causes no new required
capability-pin amendments.

## Offline preflight and limits

Five changed Bend files: 215 declarations, 62 truncated contexts and an
unavailable composition (126,361 / 48,000 bytes; 73 collaborators outside
the combined file group). The full `src/SPEC.md` task exceeds the task byte
limit. This file preflight exits 3 and cannot qualify the mechanism.
The bounded manifest completes 20 groups, 1,434 contexts, all 20 compositions,
zero truncation and zero structural blockers; zero provider requests/responses.
New catalog/core collaborators enter frontend groups as interfaces, with full
bodies in their own existing groups. The 48,000-byte cap and every style target
stay fixed. The manifest's oversized `src/SPEC.md` tasks likewise leave
potential profundity unavailable; Galaxy brain remains unrated/advisory.

Compression, Delight, Memetic identity, Anticipation and Payoff are each
**unrated**; no distribution or quality pass is claimed. Live review is
coordinator-owned. All existing laws remain; both D21 general lowering
obligations and whole-compiler core-budget fitness remain open as in REVIEW-13.
The early audit uses the supported standalone book's constructor catalog.
The modules integration must supply imported constructor declaration events
when imports become supported; no module capability is claimed here.
No provider calls, network actions, environment-file reads, pushes, merges,
rebases or other-worktree writes occur in this session.

## Full gates

`BEND_NO_TELEMETRY=1 npm run -s gates`: **34/34 passed, exit 0**,
measured **1586.468244 seconds**. All source Bend hashes
match the committed checkpoint; the new precheck receipt's entire input map
matches the final source and frozen fixtures. The final reporting commit changes
only owned evidence and the review log.

[precheck-gates.json](precheck-gates.json) retains every exact count and measured
gate duration; [precheck-verification.json](precheck-verification.json) records
offline context limits, original seed replays, wrapper checks and the partial
precheck dispositions. Empty count objects indicate that the gate reports a
status without a fixture count. All eight proof entries still print
`All terms check.` in the nest rounds.

| Gate | Status / exit | Exact counts | Measured seconds |
| --- | --- | --- | ---: |
| `frontend` | passed / 0 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` | 140.912229 |
| `checker` | passed / 0 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` | 44.112547 |
| `structural` | passed / 0 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` | 65.472604 |
| `fields` | passed / 0 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` | 131.473246 |
| `wasm` | passed / 0 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":62}` | 110.080016 |
| `wasm-trust` | passed / 0 | `{"entries":3,"proof_holes":0}` | 1.061452 |
| `fields-trust` | passed / 0 | `{"entries":4,"proof_holes":0}` | 1.329659 |
| `structural-trust` | passed / 0 | `{"entries":2,"proof_holes":0}` | 0.998317 |
| `owned-store` | passed / 0 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` | 12.171640 |
| `flat-store` | passed / 0 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` | 32.724602 |
| `recursion` | passed / 0 | `{"fixtures":19,"mutants":3}` | 81.228675 |
| `fields-wasm` | passed / 0 | `{"boundaries":30,"fixtures":8,"mutants":4}` | 149.787848 |
| `census` | passed / 0 | `{"classes":41,"declarations":884,"files":35}` | 5.196945 |
| `perch-context` | passed / 0 | `{"fixtures":33,"mutants":8}` | 40.505386 |
| `lint:verify` | passed / 0 | `{"law_rules":8,"tests":168}` | 9.255241 |
| `bootstrap` | passed / 0 | `{"corpus":1991,"mutants":54,"reached":2,"stages":8}` | 76.481263 |
| `classification` | passed / 0 | `{"fixtures":17,"mutants":6}` | 4.598720 |
| `nest` | passed / 0 | `{"accepted_books":25,"boundaries":24,"boundary_observations":24,"check_observations":76,"enum_hash_checks":100,"evaluation_values":386,"fixtures":38,"matched_frozen_outcomes":38,"mutants":6,"rejected_phase_observations":78,"seed_entry_calls":174,"seed_fixtures":40,"semantic_kills":12,"unmet_frozen_outcomes":2,"unmet_phase_observations":12,"wasm_values":386}` | 251.184870 |
| `nest-review` | passed / 0 | `{"accepted_books":15,"check_observations":58,"evaluator_values":98,"fixtures":29,"fuzz_evaluator_values":221,"fuzz_false_acceptances":0,"fuzz_false_invalid":0,"fuzz_programs":3000,"mutants":7,"rejected_phase_observations":112,"seed_calls":49,"seed_fixtures":29,"semantic_kills":14,"wasm_values":98}` | 248.529314 |
| `io-host` | passed / 0 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` | 17.741663 |
| `io-abi-2` | passed / 0 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` | 60.906441 |
| `selfhost` | passed / 0 | `{"blocked":63,"cases":65,"d4_gaps":1,"judge_mutants":20,"mutants":3,"passed":2}` | 231.656718 |
| `nest-round3` | passed / 0 | `{"accepted_books":32,"check_observations":122,"evaluator_values":164,"findings":{"dotted-binder":20,"empty-binding":25,"line-broken-header":16},"fixtures":61,"mutants":11,"rejected_phase_observations":232,"seed_calls":82,"seed_fixtures":61,"semantic_kills":22,"wasm_values":164}` | 300.159602 |
| `nest-round4` | passed / 0 | `{"accepted_books":8,"check_observations":28,"evaluator_values":64,"fixtures":14,"mutants":4,"rejected_phase_observations":48,"seed_calls":32,"seed_fixtures":14,"semantic_kills":8,"wasm_values":64}` | 150.951780 |
| `nest-round6` | passed / 0 | `{"accepted_books":11,"check_observations":70,"evaluator_values":118,"findings":{"control":11,"joined-line":5,"main-era":11,"new-row":7,"tab":1},"fixtures":35,"mutants":5,"rejected_phase_observations":192,"seed_calls":59,"seed_fixtures":35,"semantic_kills":10,"wasm_values":118}` | 168.100810 |
| `nest-round7` | passed / 0 | `{"accepted_books":20,"check_observations":70,"evaluator_values":268,"findings":{"control":19,"let-kind":1,"let-promotion":12,"parameter-alias":2,"parameter-kind":1},"fixtures":35,"generated_evaluator_values":1836,"generated_false_acceptances":0,"generated_false_invalid":0,"generated_programs":1500,"generated_seed_outcomes":{"Accepted":780,"Invalid":720},"mutants":3,"rejected_phase_observations":120,"seed_calls":134,"seed_fixtures":35,"semantic_kills":6,"wasm_values":268}` | 189.083506 |
| `nest-round8` | passed / 0 | `{"accepted_books":21,"check_observations":74,"evaluator_values":292,"findings":{"data-control":4,"default-scrutinee":2,"destructured-promotion":17,"kind-at-binding":14},"fixtures":37,"generated_evaluator_values":375,"generated_false_acceptances":0,"generated_false_invalid":0,"generated_knot_outcomes":{"Accepted":1148,"Invalid":1796,"Unsupported":56},"generated_programs":3000,"generated_promotes_type":1334,"generated_seed_outcomes":{"Accepted":1161,"Invalid":1839},"mutants":5,"rejected_phase_observations":128,"seed_calls":150,"seed_fixtures":37,"semantic_kills":10,"wasm_values":292}` | 249.997478 |
| `nest-round9` | passed / 0 | `{"accepted_books":18,"check_observations":160,"evaluator_values":188,"findings":{"dotted-binder-stopgap":8,"inferable-control":17,"layout-stopgap":7,"let-of-refined-binder":47,"literal-control":1},"fixtures":80,"mutants":12,"rejected_phase_observations":496,"seed_calls":111,"seed_fixtures":80,"semantic_kills":24,"wasm_values":188}` | 381.466820 |
| `nest-round10` | passed / 0 | `{"accepted_books":43,"check_observations":304,"evaluator_values":686,"findings":{"argument-control":1,"argument-operator":1,"argument-pattern":1,"argument-promotion":1,"argument-whitespace":8,"arrow-control":4,"arrow-gap":6,"body-layout":7,"body-layout-control":2,"let-break":10,"let-break-control":2,"marker-control":17,"marker-gap":12,"plus-row-control":22,"plus-row-gap":45,"repeated-promotion":7,"repeated-promotion-control":1,"unsupported-control":5},"fixtures":152,"mutants":22,"rejected_phase_observations":872,"seed_calls":624,"seed_fixtures":152,"semantic_kills":44,"wasm_values":686}` | 611.208549 |
| `nest-round11` | passed / 0 | `{"accepted_books":62,"check_observations":660,"evaluator_values":656,"findings":{"argument-comma":1,"argument-numeral":4,"arity-fields":12,"arity-ok":3,"arity-width":9,"dead-arity-down":7,"dead-arity-up":7,"dead-bare":7,"dead-call":7,"dead-count-up":7,"dead-deep-arity":7,"dead-deep-unknown":7,"dead-edge-arity-up":2,"dead-edge-bare":2,"dead-edge-unknown":2,"dead-lax":8,"dead-let-ok":5,"dead-ok":12,"dead-plus-ctor":7,"dead-plus-dtype":7,"dead-plus-let":4,"dead-unknown":7,"dead-wide":2,"dead-wide-ok":1,"header-invalid":2,"header-ok":1,"header-operator":3,"header-term":2,"layout-canonical":2,"layout-case-at-match":2,"layout-case-first-at-match":2,"layout-case-left-of-match":2,"layout-case-margin":2,"layout-declaration":3,"layout-declaration-deep":2,"layout-declaration-glued":4,"layout-invalid":3,"layout-later-at-case":2,"layout-later-deeper":2,"layout-later-shallower":2,"layout-later-untyped":2,"layout-match-body":2,"layout-minus-body":2,"layout-plain-split":8,"layout-plus-body":2,"layout-plus-body-shallow":2,"layout-same-line":6,"layout-split-colon-comment":2,"layout-split-colon-erased":2,"layout-split-colon-plus":2,"nat-column":22,"nat-column3":4,"nat-first":2,"nat-ok":5,"paren-break":11,"paren-break-argument":2,"paren-break-live":1,"paren-break-rejected":5,"paren-same-line-accepted":2,"paren-same-line-live":2,"paren-same-line-row":1,"plusd-constructor":4,"plusd-datatype":17,"plusd-ok":13,"plusd-order-after":1,"shadow":15,"shadow-fields":2,"shadow-later-type":1,"shadow-ok":10,"shadow-signature":7},"fixtures":330,"mutants":23,"rejected_phase_observations":2144,"seed_calls":328,"seed_fixtures":330,"semantic_kills":46,"wasm_values":656}` | 637.170849 |
| `nest-sweep11` | passed / 0 | `{"evaluator_values":1330,"false_acceptances":0,"false_invalid":0,"fixtures":0,"knot_outcomes":{"Accepted":1330,"Invalid":2810,"Unsupported":1960},"mutants":18,"programs":6100,"seed_outcomes":{"Accepted":2131,"Invalid":3969},"semantic_kills":36}` | 461.322442 |
| `nest-round12` | passed / 0 | `{"accepted_books":23,"check_observations":322,"evaluator_values":458,"false_acceptances":0,"false_invalid":0,"findings":{"plusfirst":32,"suffix":129},"fixtures":161,"knot_outcomes":{"Accepted":647,"Invalid":1211,"Unsupported":1142},"mutants":26,"programs":3000,"rejected_phase_observations":1104,"seed_calls":229,"seed_fixtures":161,"seed_outcomes":{"Accepted":1265,"Invalid":1735},"semantic_kills":52,"sweep_evaluator_values":647,"wasm_values":458}` | 577.141858 |
| `nest-round13` | passed / 0 | `{"accepted_books":3,"check_observations":420,"evaluator_values":6,"findings":{"argterm":40,"bodystart":96,"default":9,"letop":65},"fixtures":210,"grid_cells":684,"host_exhausted_modules":1,"mutants":25,"rejected_phase_observations":1656,"seed_calls":13,"seed_fixtures":210,"semantic_kills":50,"wasm_values":5,"zoo_forms":64}` | 237.199365 |
| `nest-precheck` | passed / 0 | `{"evaluator_values":4,"fixtures":10,"mutants":3,"phase_observations":100,"preserved_artifacts":32,"proof_entries":1,"seed_check_observations":10,"seed_parse_observations":10,"semantic_kills":6,"wasm_values":8}` | 92.419703 |

Fresh convergence: round 11 covers 6,100 programs / 330 classes; fuzz12 covers
3,000 / 295 classes. Both report zero false acceptances and zero false Invalid.
The frozen grid's 684 cells (57 actual reviewer terms, despite the prompt's 720;
see REVIEW-13) and the 64-form zoo likewise have zero false acceptances and zero
seed-accepted Invalid. Their exact outcome distributions are in precheck-gates.json.

`npm run -s gates:verify`: 21 tests, OK, exit 0, replayed at the final source
checkpoint. Census: current, exit 0.
Fresh receipt drift: `{"identical": 64, "semantic": 31, "volatile-only": 9}`.
Only the new `precheck.json` is copied back; historical and shared gate
receipts remain for coordinator refresh. The stopped failed snapshot is
retained as failed evidence, never counted as a passing run.

The fast C1/C3/C4 precheck at `bb8e11a9` exits 3: 23 executor major/blocking
conditions remain, comprising six binding prefix disputes, four inherited
capability exceptions and thirteen historical stale receipts. It reports no
unsafe parse acceptance, host-path condition or census red tip. Missing manifest
fields and the then-unfinished full run limit that suite's coverage. It is not
reported as green; its source audit is unchanged by `486ae5ff`.

Coordinator actions remain live semantic/style review, historical capability
exception bookkeeping, the proposed coordinator state update, merge and shared receipt refresh. Other increments own
dotted-binder scope, imported constructor events and the queued default core.
The two required D21 general laws and whole-compiler budget fitness stay open.
The selfhost qualification records two passing cases and 63 blocked cases, with
one D4 gap; fixpoint acceptance belongs to the later language and VM increments.
