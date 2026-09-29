# Perch live review of the compiler-campaign backlog

Date: 2026-09-28 (PDT; receipts are UTC 2026-09-29T04:50:55Z to 05:17:21Z). Scope: every Bend file changed on `main` from `185b7d5` (the campaign charter) to `a6367eb9`, 490 files (482 added, 8 modified). `main` stayed at `a6367eb9f434d0123ea809e81f63a853012a9fe4` from the first to the last request. All live Perch commands ran with cwd `/Users/ericfode/src/knot` (its `.env` was loaded by Perch itself and never read); no tracked file of that checkout was touched. No code was changed. Nothing was pushed or merged.

Files in this directory: [findings-ledger.md](findings-ledger.md) (all 246 semantic findings with adjudication and evidence), [style-declarations.md](style-declarations.md) (per-declaration style rows for every changed compiler, research and harness file), [style-fixtures.md](style-fixtures.md) and [style-fixtures-declarations.tsv.gz](style-fixtures-declarations.tsv.gz) (fixture suites), [receipts.tsv](receipts.tsv) (usage receipt id for every run). The log entry is in [../../perch-review-log.md](../../perch-review-log.md).

## Result

- **Confirmed defects: 0.** Of 246 reported semantic findings, 219 are false positives, 12 are duplicates, 12 are unresolved advisory refactor observations and 3 are true positives on deliberately invalid fixtures that name their intended rejection ("confirmed, intended negative control"; not defects). No accepted law or code was weakened or changed.
- One naming/strength follow-up (FU-1) and one tooling limit (FU-2, `src/SPEC.md` over the 16 KB task cap) are recorded below. No authentication or quota failure occurred.
- **Style:** rubric v8 was run live on all 14 explicit source groups (8 compiler manifest groups, research, harness) and on 14 fixture suites. No composition is a style pass: all 14 explicit compositions miss the payoff target (7 below, 7 uncertain). At declaration level 29 of the 101 changed compiler declarations meet all five role-scaled targets. All below-target and uncertain results stand; none was "fixed" and none is reported as a pass.
- Coverage limits: 44 fixtures are rejected by the pinned Bend parser (the seed's `--check-only` rejects all 44 too; they are negative or malformed-by-design inputs) and have zero coverage in both reviews, not counted as clean; 7 datatype-only files have no executable declaration (semantic review not applicable, style-rated on their 13 datatypes). Three generated stress fixtures (`deep-call`, `deep-stack`, `scale-catalog`) are too large for a style context. Details below.

## Method and identities

| item | value |
| --- | --- |
| Perch | `@lakeday/perch` 0.3.5, Bend adapter parser `bend-2.0.29-574b6d3-observer-v3+law-template-arity` |
| requested / resolved model | `jev-latest` / `jev-1.13.0` (every request; observed this run, not cached) |
| semantic rules hash (`rules_sha256`) | `7879db5b57067b4f0237cd80da969cd1e79adbd61fda600351f6bfd6d45f0506` (13 source rules plus built-in questions; the 00:45 wave-1 receipts used another hash) |
| style rubric | v8 `b0747948ceadd3c10f48634adeccc2c880d944a9e63b1f6906d6121a68f4d693`, endpoint sha `17abdbd0…5830e9` |
| semantic command | `npm run -s lint -- <file>` per file (every parsed declaration, all rules; wave-1 `--rules` subsets were not reused) |
| style command, compiler | `npm run -s lint:style -- --live --incremental --manifest=docs/compiler-campaign/manifest.json --group=<g>` for the 8 groups that select a changed file in full |
| style command, others | `npm run -s lint:style -- --live --incremental --context=interfaces-v1 [--task=<spec>] <files>`. Deliberate deviation from the brief's `--task=src/SPEC.md <file>`: that file is over the 16 KB task cap (`task_byte_limit`, FU-2) and is not these files' contract, so each research, harness and fixture group used its own spec or suite document (or none where that is over the cap), and `interfaces-v1` avoids the legacy datatype and helper truncation seen in preflight |
| requests | 9,074 semantic (50,474 unit checks) and 4,555 style; 13,629 in all; 490 semantic and 28 style receipts |
| elapsed | first to last receipt 26 min 26 s of wall clock, including adjudication pauses (measured from receipt timestamps, not from attempts) |
| deterministic checks | pinned seed `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts`, `BEND_NO_TELEMETRY=1`, run from a scratch worktree with the toolchain symlinked (unlinked afterwards) |

`--incremental` reused identical requests only inside this session (compiler groups sharing declarations: 41 in `frontend-laws`, 99 in `checking`, 10 in `fields-laws`, 19 in `wasm-emission`); those are reused answers, not new reviews. No earlier v8 live style run existed, so nothing older was reused. Groups not run: `syntax-core`, `frontend-lexing`, `diagnostics`, `catalog`, `evaluation`, `wasm-codec`, `driver-pipeline`, `runtime-laws`, `catalog-laws` (they select only unchanged files in full; changed files enter them as interface-only context). The unfiltered manifest was not run.

## Coverage

| class | files | semantic (`lint`) | style |
| --- | --- | --- | --- |
| compiler `src/` | 9 | all 9, every parsed declaration | manifest groups `recursion-laws`, `frontend-parsing`, `frontend-laws`, `scope-patterns`, `checking`, `checker-laws`, `fields-laws`, `wasm-emission` |
| research (adaptive runtime, data-lifetime) | 8 | all 8 | explicit groups `adaptive-runtime`, `data-lifetime` |
| test harness Bend | 6 | all 6 | groups `fields-wasm` (3 files), `fields-bounds`, `io-read-bytes`, `io-empty-write` |
| authored fixtures (data-lifetime 4, fields-wasm 8, perch-context 1, census 3) | 16 | all 16 | 14 files; `deep-call` and `deep-stack` are generated and too large |
| compiler test fixtures (`tests/compiler-*`, `tests/subsets`) | 451 | 400 reviewed, 44 parse-rejected, 7 no executable declaration | 406 files in 10 suites |

Not reviewed (not Bend): changed `LAW_REVIEW.md` packets, `.py`, `.json`, `.wat`, `.mjs` and `.c` files.

## Semantic results, authored files

Adjudication per file (a finding is one flagged declaration and label; the full rows are in the ledger). Receipt ids are shortened here.

### Compiler source

| file | decls | unit checks | requests | findings | adjudication | receipt |
| --- | --- | --- | --- | --- | --- | --- |
| `src/LAWS.bend` | 16 | 224 | 32/32 | 1 | 1 false-positive | `04-51-47…ef06505f` |
| `src/PROOF.bend` | 16 | 224 | 32/32 | 29 | 29 false-positive | `04-51-51…7593bfe5` |
| `src/check.bend` | 34 | 476 | 68/68 | 2 | 2 unresolved | `04-51-55…cbe1c1cf` |
| `src/parse.bend` | 20 | 280 | 40/40 | 2 | 2 unresolved | `04-52-01…9e35bad7` |
| `src/patterns.bend` | 9 | 126 | 18/18 | 2 | 2 unresolved | `04-52-05…7e01f671` |
| `src/recursion-LAWS.bend` | 16 | 224 | 32/32 | 1 | 1 false-positive | `04-51-43…f2ecf8d1` |
| `src/recursion-PROOF.bend` | 16 | 224 | 32/32 | 21 | 21 false-positive | `04-50-55…1b5715dc` |
| `src/scope.bend` | 23 | 322 | 46/46 | 2 | 2 unresolved | `04-52-09…179d4938` |
| `src/wasm.bend` | 39 | 546 | 78/78 | 3 | 1 false-positive, 2 unresolved | `04-52-13…61b7fd27` |

### Research

| file | decls | unit checks | requests | findings | adjudication | receipt |
| --- | --- | --- | --- | --- | --- | --- |
| `research/adaptive-tasks/runtime/LAWS.bend` | 8 | 88 | 16/16 | 1 | 1 false-positive | `04-52-18…69712957` |
| `research/adaptive-tasks/runtime/PROOF.bend` | 8 | 88 | 16/16 | 8 | 8 false-positive | `04-52-22…7863e6be` |
| `research/adaptive-tasks/runtime/frontier.bend` | 31 | 341 | 62/62 | 3 | 3 false-positive | `04-52-25…09f3b613` |
| `research/adaptive-tasks/runtime/slot-model.bend` | 6 | 66 | 12/12 | 0 | clean | `04-52-29…a7489d0f` |
| `research/data-lifetime/LAWS.bend` | 20 | 220 | 40/40 | 1 | 1 false-positive | `04-52-32…245550fc` |
| `research/data-lifetime/PROOF.bend` | 20 | 220 | 40/40 | 13 | 13 false-positive | `04-52-36…471ecde3` |
| `research/data-lifetime/model.bend` | 62 | 682 | 124/124 | 3 | 1 false-positive, 2 unresolved | `04-52-40…b86a5aef` |
| `research/data-lifetime/observe.bend` | 7 | 77 | 14/14 | 0 | clean | `04-52-45…1be8ebdb` |

### Test harness and authored fixtures

| file | decls | unit checks | requests | findings | adjudication | receipt |
| --- | --- | --- | --- | --- | --- | --- |
| `research/data-lifetime/fixtures/list-tail.bend` | 2 | 22 | 4/4 | 0 | clean | `04-53-45…746444db` |
| `research/data-lifetime/fixtures/owned-rebuild.bend` | 2 | 22 | 4/4 | 0 | clean | `04-53-47…4c8a1736` |
| `research/data-lifetime/fixtures/shared-open.bend` | 2 | 22 | 4/4 | 0 | clean | `04-53-49…b035a457` |
| `research/data-lifetime/fixtures/tree-share.bend` | 2 | 22 | 4/4 | 0 | clean | `04-53-52…4ab717ff` |
| `tests/compiler-fields-wasm/LAWS.bend` | 5 | 55 | 10/10 | 0 | clean | `04-52-48…8e4eb277` |
| `tests/compiler-fields-wasm/PROOF.bend` | 5 | 55 | 10/10 | 3 | 3 false-positive | `04-52-52…385908ff` |
| `tests/compiler-fields-wasm/compile.bend` | 4 | 44 | 8/8 | 0 | clean | `04-52-54…37b629e6` |
| `tests/compiler-fields-wasm/fixtures/aliasing.bend` | 3 | 33 | 6/6 | 1 | 1 false-positive | `04-53-54…2d42a198` |
| `tests/compiler-fields-wasm/fixtures/arena-overflow.bend` | 17 | 187 | 34/34 | 0 | clean | `04-53-57…065af98f` |
| `tests/compiler-fields-wasm/fixtures/deep-call.bend` | 251 | 2761 | 502/502 | 0 | clean | `04-54-00…dd6d6b82` |
| `tests/compiler-fields-wasm/fixtures/deep-stack.bend` | 161 | 1771 | 322/322 | 0 | clean | `04-54-10…62376d80` |
| `tests/compiler-fields-wasm/fixtures/erased.bend` | 6 | 66 | 12/12 | 0 | clean | `04-54-20…63cb8871` |
| `tests/compiler-fields-wasm/fixtures/nested.bend` | 4 | 44 | 8/8 | 0 | clean | `04-54-23…124efdc1` |
| `tests/compiler-fields-wasm/fixtures/pair.bend` | 5 | 55 | 10/10 | 0 | clean | `04-54-26…769a66e7` |
| `tests/compiler-fields-wasm/fixtures/peano.bend` | 5 | 55 | 10/10 | 0 | clean | `04-54-28…f9209367` |
| `tests/compiler-fields/bounds.bend` | 4 | 44 | 8/8 | 0 | clean | `04-52-59…787faa13` |
| `tests/compiler-io-abi-2/read-bytes.bend` | 12 | 132 | 24/24 | 0 | clean | `04-53-02…047174b5` |
| `tests/compiler-io/host/empty-write.bend` | 7 | 77 | 14/14 | 0 | clean | `04-53-05…288df259` |
| `tests/perch-context/fixtures/signatures.bend` | 11 | 121 | 22/22 | 0 | clean | `04-54-31…e2c30c39` |
| `tools/census/fixtures/control.bend` | 1 | 11 | 2/2 | 0 | clean | `04-54-34…a5576c1d` |
| `tools/census/fixtures/features.bend` | 10 | 110 | 20/20 | 4 | 4 false-positive | `04-54-36…c7d5b15a` |
| `tools/census/fixtures/lambda.bend` | 2 | 22 | 4/4 | 0 | clean | `04-54-39…e1a92301` |

### Compiler test fixtures (summary)

| suite | files | reviewed | parse-rejected | no executable declaration | files with findings | findings |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/compiler-baseslice` | 40 | 40 | 0 | 0 | 17 | 22 |
| `tests/compiler-closures` | 42 | 40 | 2 | 0 | 11 | 23 |
| `tests/compiler-generics` | 40 | 40 | 0 | 0 | 6 | 14 |
| `tests/compiler-io` | 40 | 40 | 0 | 0 | 16 | 26 |
| `tests/compiler-literals` | 40 | 31 | 9 | 0 | 5 | 8 |
| `tests/compiler-poly` | 61 | 60 | 1 | 0 | 9 | 16 |
| `tests/compiler-recursion` | 19 | 19 | 0 | 0 | 7 | 10 |
| `tests/compiler-selfhost` | 99 | 85 | 8 | 6 | 11 | 11 |
| `tests/compiler-sugar` | 40 | 35 | 5 | 0 | 6 | 9 |
| `tests/subsets/classification` | 30 | 10 | 19 | 1 | 6 | 7 |
| **total** | 451 | 400 | 44 | 7 | 94 | 146 |

## Adjudication

Vocabulary: **confirmed** (proved or reproduced), **false-positive**, **duplicate**, **unresolved**. Evidence ids E1 to E10 are defined in the [ledger](findings-ledger.md#evidence).

| class | findings | judgment | basis |
| --- | --- | --- | --- |
| built-in `does_not_do_what_it_claims` (53), `dead_code` (16), `docs` (3) and custom `bend-machine-arithmetic` (2) on `{==}` law fills (5 proof entries) | 74 | false-positive | E1 seed accepts every fill against its law; E2 a wrong law under the same fill is rejected; E3 all laws are filled. The `docs` flags (3) are judged only on the fill being a one-line entry whose law carries the comment; seed acceptance is not evidence about documentation |
| law statements (`generic_header` error_ignored, `root_fields_are_smaller`, `zero_slice`, `count_ceiling_preserves_state`) | 4 | false-positive | E1, E2, E6; the comment or SPEC states the behaviour. `count_ceiling_preserves_state` has a naming/strength note (FU-1), and E5 shows the property holds |
| `integer_overflow` (`wasm.allocate`, `data-lifetime allocate`) | 2 | false-positive | E7 bounds and E4 boundary probes |
| adaptive runtime `offer`/`publish` | 3 | false-positive | E6: 186 independent phase observations agree, 7 mutants killed |
| authored fixtures (`aliasing.observe`, census `features.text` ×3, `float`) | 5 | false-positive | E8 frozen literals |
| advisory refactors on compiler/research code (`tangled_conditions` ×8, `too_big` ×2, `too_nested` ×2) | 12 | unresolved | verified sizes (`run` 55 lines, `lower` 52), no behaviour claim; the fuel/mode dispatch is the documented idiom (SELF-HOSTING-PATH.md, "Fuel dispatch"). Advisory backlog only |
| `bend-machine-arithmetic` on compiler fixtures | 43 (+8 mirrors) | false-positive / duplicate | E10: no arithmetic in any flagged declaration; p 0.81 to 0.86 against the 0.80 floor |
| built-in defects, security, refactor on fixtures | 88 | false-positive / duplicate | E9 seed status and frozen expectations, E10 reading; `missing_authorization` / `resource_exhaustion` on argv-path IO programs are out of scope |
| intended negative controls | 3 (+3 duplicates of them) | confirmed (intended negative control) | `wrong-type-arg.main` type_confusion, `rigid-domain-mismatch.compose` wrong_order, `result-missing-fail.opened` bend-effect-boundary; each label names the fixture's stated rejection (E9, E10) |

Per-rule precision over adjudicated findings, jev-1.13.0: custom `bend-machine-arithmetic` 0 confirmed of 46 deduplicated (all p 0.81 to 0.86, just above its 0.80 floor, all on declarations without arithmetic; its question lacks the "if none, this rule holds" clause that the other Bend rules end with); built-in `does_not_do_what_it_claims` 0 confirmed of 81 false positives (2 duplicates; p 0.71 to 0.92; 53 of the 83 are on `{==}` fills). The other rules had no adjudicated true positive except the three controls above. This is the recurrence of the `L.put_empty` false positive recorded on 2026-09-27; see the log entry.

## Follow-ups (none is a confirmed defect)

- **FU-1** (`research/data-lifetime/LAWS.bend`, data-lifetime owner, low): `count_ceiling_preserves_state` states only `Fail{3}`. Rename it (for example `count_ceiling_is_exhausted`) or add the composed law verified in E5: `M.commit(M.share(<heap at ceiling>,0,1),<same heap>) == (<same heap>,3)`. The implementation is correct.
- **FU-2** (tooling, coordinator): `src/SPEC.md` is 20,417 bytes and the task cap is 16 KB, so potential profundity is `unavailable` and Galaxy brain stays advisory in 10 of the 17 manifest groups (four were run here: `frontend-parsing`, `frontend-laws`, `checker-laws`, `wasm-emission`). Decide between a task summary file and a cap change; do not trim the SPEC.
- **FU-3** (Perch maintenance trigger, proposal only): (a) built-in defect/refactor/docs questions on `{==}` law fills recur at p 0.71 to 0.92 despite the paired law being supplied; propose skipping those questions for `law_fill` units (or adding the seed's acceptance as context), never raising a floor. (b) `bend-machine-arithmetic`: done afterwards on branch `perch/arithmetic-rule` (applicability sentence, concrete violation shapes, floor 0.70, controls in `tests/perch-arithmetic`); see the review log. No rule or floor was edited in this review's own commit.
- **FU-4** (advisory backlog, refactor observations): `check.bend` `call_result:76` and `run:174`; `parse.bend` `parameter_end:88` and `term_failure:138` (a six-way `or` over terminator tokens); `patterns.bend` `quantity:10` and `fields:33`; `scope.bend` `occurrence:55` and `matchable:126`; `wasm.bend` `lower:141` and `extend_sections:215`; `research/data-lifetime/model.bend` `gather:98` and `allocate:160`. Take these only with a concrete reading hypothesis from the style campaign; none affects behaviour.
- **FU-5** (style calibration, unresolved): all 14 explicit compositions miss payoff, including `recursion-laws` at 8% although the seed accepts every proof. The interface-only context forbids inferring proof execution, which may cap payoff for law/proof mechanisms; counter-context: the `io` fixture suite, which has no proofs, ran under the same context rule and met its composition payoff target. Record as one calibration observation, not 14 failures.

## Style results

Rubric v8, `jev-1.13.0`. Every declaration is judged on the five axes at its role-scaled target (leading and uncertain roles at level 3, supporting helpers at level 2 for memetic, anticipation and payoff). "Meet all five" is the number of declarations with every target met; composition is the group's own memetic, anticipation and payoff. Nothing here is a semantic verdict or a pass. Cells: ✓ meets, ✗ below, ? uncertain, percent at target.

### Explicit groups

| group | selected in full | decls (all reviewed) | meet all five | changed decls meeting all | composition (memetic / anticipation / payoff) | potential | task | requests (cache hits) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `recursion-laws` | `src/recursion-LAWS.bend`, `src/recursion-PROOF.bend` | 32 | 13 | 13/32 | below_target (✓90 / ✓92 / ✗8) | low 4% | yes | 34 (0) |
| `frontend-parsing` | `src/parse.bend` | 41 | 16 | 3/5 | below_target (✓76 / ✗39 / ?57) | unavailable | SPEC.md over 16 KB cap | 42 (0) |
| `frontend-laws` | `src/LAWS.bend`, `src/parse.bend`, `src/PROOF.bend` | 81 | 17 | 3/29 | below_target (✓86 / ?59 / ✗20) | unavailable | SPEC.md over 16 KB cap | 41 (41) |
| `scope-patterns` | `src/scope.bend`, `src/patterns.bend` | 99 | 40 | 6/13 | uncertain (✓92 / ✓87 / ?46) | low 18% | yes | 101 (0) |
| `checking` | `src/scope.bend`, `src/patterns.bend`, `src/check.bend` | 134 | 56 | 8/17 | uncertain (✓88 / ✓86 / ?49) | low 18% | yes | 36 (99) |
| `checker-laws` | `src/scope.bend` | 38 | 6 | 0/10 | below_target (✓79 / ✓75 / ✗27) | unavailable | SPEC.md over 16 KB cap | 39 (0) |
| `fields-laws` | `src/patterns.bend` | 32 | 17 | 2/3 | below_target (✓94 / ✓91 / ✗35) | low 18% | yes | 23 (10) |
| `wasm-emission` | `src/wasm.bend` | 89 | 22 | 5/23 | uncertain (✓86 / ✓63 / ?44) | unavailable | SPEC.md over 16 KB cap | 71 (19) |
| `adaptive-runtime` | `research/adaptive-tasks/runtime/LAWS.bend`, `research/adaptive-tasks/runtime/PROOF.bend`, `research/adaptive-tasks/runtime/frontier.bend`, `research/adaptive-tasks/runtime/slot-model.bend` | 57 | 19 | 19/57 | uncertain (✓91 / ✓89 / ?43) | low 13% | yes | 59 (0) |
| `data-lifetime` | `research/data-lifetime/LAWS.bend`, `research/data-lifetime/PROOF.bend`, `research/data-lifetime/model.bend`, `research/data-lifetime/observe.bend` | 117 | 40 | 40/117 | uncertain (✓95 / ✓93 / ?46) | low 25% | yes | 119 (0) |
| `fields-wasm` | `tests/compiler-fields-wasm/LAWS.bend`, `tests/compiler-fields-wasm/PROOF.bend`, `tests/compiler-fields-wasm/compile.bend` | 14 | 8 | 8/14 | below_target (✓75 / ✓73 / ✗17) | low 6% | yes | 16 (0) |
| `fields-bounds` | `tests/compiler-fields/bounds.bend` | 4 | 0 | 0/2 | below_target (?47 / ✓68 / ✗2) | low 18% | yes | 5 (0) |
| `io-read-bytes` | `tests/compiler-io-abi-2/read-bytes.bend` | 12 | 0 | 0/12 | below_target (✗30 / ✓63 / ✗25) | low 7% | yes | 14 (0) |
| `io-empty-write` | `tests/compiler-io/host/empty-write.bend` | 7 | 0 | 0/7 | below_target (✗19 / ?42 / ?48) | unavailable | none | 8 (0) |

`task` reads "yes" when the fixed task file was within the 16 KB cap. `changed decls meeting all` counts declarations that overlap a change in `185b7d5..a6367eb9` (all declarations of an added file). Unchanged context files that these groups also reviewed are in the declaration totals but not in the changed counts.

### Changed compiler declarations (primary group per file)

Across the 101 changed declarations: 29 meet all five. Per axis, met / below / uncertain: big brain 65/18/18, delight 76/9/16, memetic 47/40/14, anticipation 51/22/28, payoff 45/39/17. The weakest are `src/LAWS.bend` and `src/PROOF.bend` (0 of 24), `wasm.bend` (5 of 23) and the new recursion laws and proofs (13 of 32). `check.bend` (2 of 4), `parse.bend` (3 of 5) and `patterns.bend` (2 of 3) changed little. Δ marks a changed declaration.

#### `src/parse.bend` (group `frontend-parsing`): 22 declarations, 5 changed, 3 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `starts`:33 Δ | definition | supp | ✓90 | ✓75 | ✓68 | ✓95 | ✓95 | ✓ |
| `scrutinee`:38 Δ | definition | supp | ✓83 | ✓71 | ✓63 | ✓88 | ✓91 | ✓ |
| `template_parameter`:113 Δ | definition | supp | ✓62 | ✓69 | ✓83 | ✓96 | ✓93 | ✓ |
| `reply`:127 Δ | definition | supp | ✗40 | ?48 | ✓76 | ?56 | ✓83 | ✗ |
| `run`:148 Δ | definition | lead | ✗31 | ✓79 | ✓60 | ✓73 | ✓73 | ✗ |

#### `src/LAWS.bend` (group `frontend-laws`): 16 declarations, 12 changed, 0 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `generic_header`:25 Δ | law | unc | ?53 | ✓72 | ✗35 | ✗35 | ✗32 | ✗ |
| `multiple_scrutinees`:31 Δ | law | lead | ?47 | ✓62 | ✗39 | ✗25 | ✗29 | ✗ |
| `template_binder`:37 Δ | law | lead | ?51 | ✓62 | ✗36 | ✗26 | ✗21 | ✗ |
| `nonleading_template_binder`:43 Δ | law | unc | ✓63 | ✓63 | ✗23 | ✗22 | ✗24 | ✗ |
| `destructuring_binding`:50 Δ | law | lead | ?58 | ?49 | ✗16 | ✗38 | ✗37 | ✗ |
| `equality_is_not_binding`:58 Δ | law | lead | ✓63 | ?51 | ✗18 | ✗35 | ?41 | ✗ |
| `arrow_is_not_binding`:65 Δ | law | lead | ✓65 | ?59 | ✗18 | ?43 | ?44 | ✗ |
| `parameter_type_application`:72 Δ | law | lead | ✗32 | ?45 | ✗18 | ✗26 | ✗28 | ✗ |
| `return_type_application`:78 Δ | law | unc | ?52 | ✓65 | ✗38 | ✗32 | ?42 | ✗ |
| `binding_type_application`:85 Δ | law | unc | ?49 | ✓66 | ✗30 | ✗36 | ✗33 | ✗ |
| `local_import`:91 Δ | law | supp | ?50 | ✓71 | ✓90 | ✓77 | ✓69 | ✗ |
| `hash_import`:97 Δ | law | supp | ?53 | ✓65 | ✓83 | ✓66 | ✓64 | ✗ |

#### `src/PROOF.bend` (group `frontend-laws`): 16 declarations, 12 changed, 0 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.generic_header`:22 Δ | law_fill | supp | ✗20 | ?48 | ✓63 | ?52 | ✗19 | ✗ |
| `L.multiple_scrutinees`:25 Δ | law_fill | unc | ✗14 | ✗36 | ✗29 | ?50 | ✗12 | ✗ |
| `L.template_binder`:28 Δ | law_fill | unc | ✗15 | ✗33 | ✗28 | ✗35 | ✗10 | ✗ |
| `L.nonleading_template_binder`:31 Δ | law_fill | unc | ✗18 | ✗36 | ✗18 | ?49 | ✗07 | ✗ |
| `L.destructuring_binding`:34 Δ | law_fill | unc | ✓63 | ✓61 | ✗17 | ?50 | ?51 | ✗ |
| `L.equality_is_not_binding`:42 Δ | law_fill | lead | ✗08 | ✗30 | ✗16 | ✓74 | ✗08 | ✗ |
| `L.arrow_is_not_binding`:45 Δ | law_fill | lead | ✗06 | ✗24 | ✗13 | ✓69 | ✗04 | ✗ |
| `L.parameter_type_application`:48 Δ | law_fill | lead | ✗14 | ✗37 | ✗24 | ?53 | ✗08 | ✗ |
| `L.return_type_application`:51 Δ | law_fill | unc | ✗15 | ✗37 | ✗31 | ?44 | ✗10 | ✗ |
| `L.binding_type_application`:54 Δ | law_fill | unc | ✗19 | ✗37 | ✗23 | ?49 | ✗14 | ✗ |
| `L.local_import`:57 Δ | law_fill | supp | ✗23 | ?42 | ?56 | ?55 | ✗18 | ✗ |
| `L.hash_import`:60 Δ | law_fill | supp | ✗21 | ?41 | ?54 | ?54 | ✗16 | ✗ |

#### `src/scope.bend` (group `scope-patterns`): 24 declarations, 10 changed, 4 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Scope`:5 Δ | datatype | lead | ✓68 | ✓76 | ✗23 | ?46 | ✗16 | ✗ |
| `descendants`:14 Δ | definition | unc | ✓84 | ✓74 | ✗15 | ?45 | ✗27 | ✗ |
| `descends`:18 Δ | definition | supp | ✓91 | ✓75 | ✓67 | ✓94 | ✓89 | ✓ |
| `lookup`:51 Δ | definition | supp | ✓60 | ✓68 | ✓92 | ✓96 | ✓90 | ✓ |
| `reference`:63 Δ | definition | supp | ✓87 | ✓70 | ✓89 | ✓92 | ✓90 | ✓ |
| `live_scope`:68 Δ | definition | supp | ✓98 | ✓66 | ?55 | ✓88 | ✓78 | ✗ |
| `extend`:72 Δ | definition | supp | ✓92 | ?58 | ✓76 | ✓91 | ✓81 | ✗ |
| `branch`:116 Δ | definition | lead | ✓78 | ✓88 | ?41 | ?44 | ?42 | ✗ |
| `parameters`:120 Δ | definition | lead | ✓87 | ✓74 | ✗12 | ?45 | ✗16 | ✗ |
| `matchable`:126 Δ | definition | supp | ✓77 | ✓66 | ✓91 | ✓92 | ✓92 | ✓ |

#### `src/patterns.bend` (group `scope-patterns`): 10 declarations, 3 changed, 2 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `add`:14 Δ | definition | supp | ✓77 | ✓60 | ✓91 | ✓68 | ✓89 | ✓ |
| `finish`:52 Δ | definition | supp | ✓66 | ✓76 | ✓96 | ✓84 | ✓90 | ✓ |
| `branch`:65 Δ | definition | lead | ✓63 | ✓76 | ?48 | ✗39 | ?50 | ✗ |

#### `src/check.bend` (group `checking`): 35 declarations, 4 changed, 2 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `callable`:70 Δ | definition | supp | ✓74 | ✓68 | ✓90 | ✓97 | ✓94 | ✓ |
| `call_result`:76 Δ | definition | supp | ✓79 | ✓64 | ✓85 | ✓74 | ✓88 | ✓ |
| `call_body`:141 Δ | definition | supp | ?51 | ✓64 | ✓94 | ✓95 | ✓71 | ✗ |
| `run`:174 Δ | definition | lead | ?47 | ✓74 | ✓72 | ✓70 | ✗19 | ✗ |

#### `src/wasm.bend` (group `wasm-emission`): 45 declarations, 23 changed, 5 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Profile`:14 Δ | datatype | lead | ✓64 | ?42 | ✗06 | ✗18 | ✗09 | ✗ |
| `Mode`:17 Δ | datatype | lead | ?44 | ✓87 | ✗24 | ?52 | ✗20 | ✗ |
| `fielded`:25 Δ | definition | supp | ✓75 | ✓64 | ✓72 | ✓73 | ✓92 | ✓ |
| `heap_types`:31 Δ | definition | lead | ✓91 | ✓83 | ✗12 | ✗21 | ✗17 | ✗ |
| `boxed`:37 Δ | definition | supp | ✓94 | ✓76 | ?56 | ✓91 | ✓99 | ✗ |
| `fielded_arms`:44 Δ | definition | supp | ✓80 | ✓87 | ✓74 | ✓87 | ✓93 | ✓ |
| `capability`:50 Δ | definition | supp | ✓77 | ✓65 | ?56 | ✓63 | ✓85 | ✗ |
| `memory`:122 Δ | definition | supp | ✓82 | ✓88 | ✓87 | ✓80 | ✓86 | ✓ |
| `load`:125 Δ | definition | supp | ✓85 | ✓80 | ✓90 | ✓86 | ✓93 | ✓ |
| `stores`:128 Δ | definition | lead | ✓78 | ✓80 | ✗19 | ✗10 | ✗18 | ✗ |
| `allocate`:134 Δ | definition | supp | ?55 | ?49 | ✓89 | ✓67 | ✓87 | ✗ |
| `lower`:141 Δ | definition | lead | ?48 | ✓90 | ✓72 | ?52 | ?49 | ✗ |
| `body`:204 Δ | definition | lead | ?48 | ✓88 | ?47 | ✗36 | ✗33 | ✗ |
| `entry`:223 Δ | definition | lead | ?52 | ✓75 | ✗25 | ✗38 | ✗38 | ✗ |
| `entries`:231 Δ | definition | lead | ✓64 | ✓74 | ✗12 | ✗30 | ✗17 | ✗ |
| `allocator`:240 Δ | definition | lead | ✗33 | ?43 | ✗12 | ✗28 | ✗15 | ✗ |
| `heap_sections`:245 Δ | definition | supp | ✓74 | ✓78 | ✓86 | ✓92 | ✓93 | ✓ |
| `module_bytes`:253 Δ | definition | lead | ✓72 | ✓84 | ✗32 | ?51 | ✗31 | ✗ |
| `finish`:258 Δ | definition | lead | ?55 | ✓71 | ✗21 | ✗36 | ✗30 | ✗ |
| `present`:267 Δ | definition | supp | ✓83 | ✓69 | ✗37 | ✓87 | ✓93 | ✗ |
| `profiled`:272 Δ | definition | lead | ?52 | ?52 | ✗16 | ✗27 | ✗19 | ✗ |
| `emit_profile`:278 Δ | definition | lead | ✗39 | ✓74 | ✗24 | ✗40 | ✗28 | ✗ |
| `emit`:284 Δ | definition | supp | ✓74 | ?51 | ✓62 | ✓73 | ✓92 | ✗ |

#### `src/recursion-LAWS.bend` (group `recursion-laws`): 16 declarations, 16 changed, 6 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `root_fields_are_smaller`:10 Δ | law | lead | ✓85 | ✓74 | ✗36 | ?51 | ✗38 | ✗ |
| `descendant_fields_are_smaller`:15 Δ | law | unc | ✓86 | ✓74 | ✗29 | ?55 | ?46 | ✗ |
| `unrelated_fields_stay_unmarked`:19 Δ | law | supp | ✓93 | ✓82 | ✓93 | ✓96 | ✓83 | ✓ |
| `marked_reference_descends`:23 Δ | law | unc | ✓94 | ✓76 | ✗21 | ?58 | ✓75 | ✗ |
| `root_reference_does_not_descend`:29 Δ | law | supp | ✓93 | ✓80 | ✓91 | ✓96 | ✓86 | ✓ |
| `rebuilt_argument_does_not_descend`:35 Δ | law | unc | ✓86 | ✓64 | ✗24 | ?50 | ?54 | ✗ |
| `computed_argument_does_not_descend`:44 Δ | law | supp | ✓89 | ✓74 | ✓91 | ✓94 | ✓76 | ✓ |
| `empty_call_does_not_descend`:52 Δ | law | supp | ✓93 | ✓80 | ✓88 | ✓99 | ✓90 | ✓ |
| `later_argument_cannot_establish_descent`:56 Δ | law | supp | ✓92 | ✓79 | ✓92 | ✓96 | ✓84 | ✓ |
| `local_binding_preserves_descent`:61 Δ | law | supp | ✓94 | ✓73 | ✓87 | ✓95 | ✓91 | ✓ |
| `opening_root_records_descent`:73 Δ | law | unc | ✓82 | ✓81 | ?53 | ?52 | ✓79 | ✗ |
| `opening_descendant_records_descent`:81 Δ | law | unc | ✓84 | ✓79 | ?50 | ?56 | ✓81 | ✗ |
| `descending_self_call_is_checked`:89 Δ | law | lead | ✓76 | ✓67 | ?52 | ?51 | ?51 | ✗ |
| `nondecreasing_self_call_is_unsupported`:97 Δ | law | lead | ✓81 | ✓69 | ?50 | ✓66 | ✓73 | ✗ |
| `earlier_call_needs_no_descent`:106 Δ | law | unc | ✓72 | ✓66 | ✗38 | ✗36 | ✗32 | ✗ |
| `recursive_evaluation_exhaustion`:115 Δ | law | unc | ?53 | ?49 | ✗22 | ?51 | ✗21 | ✗ |

#### `src/recursion-PROOF.bend` (group `recursion-laws`): 16 declarations, 16 changed, 7 of the changed meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.root_fields_are_smaller`:7 Δ | law_fill | supp | ✓76 | ✓72 | ✓92 | ✓76 | ✓62 | ✓ |
| `L.descendant_fields_are_smaller`:8 Δ | law_fill | supp | ✓73 | ✓62 | ✓90 | ✓72 | ?53 | ✗ |
| `L.unrelated_fields_stay_unmarked`:9 Δ | law_fill | supp | ✓72 | ✓72 | ✓86 | ✓73 | ✓62 | ✓ |
| `L.marked_reference_descends`:10 Δ | law_fill | supp | ✓86 | ✓69 | ✓86 | ✓86 | ✓60 | ✓ |
| `L.root_reference_does_not_descend`:11 Δ | law_fill | supp | ✓74 | ✓68 | ✓84 | ✓85 | ✓62 | ✓ |
| `L.rebuilt_argument_does_not_descend`:12 Δ | law_fill | supp | ✓72 | ✓66 | ✓90 | ✓84 | ?57 | ✗ |
| `L.computed_argument_does_not_descend`:13 Δ | law_fill | supp | ✓69 | ✓61 | ✓92 | ✓90 | ?53 | ✗ |
| `L.empty_call_does_not_descend`:14 Δ | law_fill | supp | ✓83 | ✓67 | ✓83 | ✓89 | ✓69 | ✓ |
| `L.later_argument_cannot_establish_descent`:15 Δ | law_fill | supp | ✓60 | ✓63 | ✓88 | ✓70 | ?50 | ✗ |
| `L.local_binding_preserves_descent`:16 Δ | law_fill | supp | ✓77 | ✓62 | ✓85 | ✓85 | ?55 | ✗ |
| `L.opening_root_records_descent`:17 Δ | law_fill | supp | ✓76 | ✓85 | ✓95 | ✓90 | ✓72 | ✓ |
| `L.opening_descendant_records_descent`:18 Δ | law_fill | supp | ✓75 | ✓83 | ✓93 | ✓88 | ✓70 | ✓ |
| `L.descending_self_call_is_checked`:19 Δ | law_fill | unc | ✓68 | ✓67 | ?50 | ?45 | ?42 | ✗ |
| `L.nondecreasing_self_call_is_unsupported`:20 Δ | law_fill | unc | ✓72 | ✓63 | ?42 | ?41 | ?41 | ✗ |
| `L.earlier_call_needs_no_descent`:21 Δ | law_fill | supp | ✗31 | ✗37 | ✓78 | ✓61 | ✗19 | ✗ |
| `L.recursive_evaluation_exhaustion`:24 Δ | law_fill | supp | ✗27 | ?46 | ✓77 | ✓64 | ✗23 | ✗ |

The remaining declarations of the changed compiler files (unchanged ones, and the rows from the other groups that select the same files in full) are in [style-declarations.md](style-declarations.md).

### Changed research and harness declarations

All of these files are new or changed code (not fixtures), so every declaration is listed. Legend as above; every declaration of an added file is changed.

#### Group `adaptive-runtime`: composition uncertain (memetic ✓91 / anticipation ✓89 / payoff ?43)

`research/adaptive-tasks/runtime/slot-model.bend`: 7 declarations, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Command`:7 Δ | datatype | supp | ?59 | ?53 | ✓68 | ?55 | ✓65 | ✗ |
| `event`:10 Δ | definition | supp | ✓84 | ?59 | ✓76 | ✓91 | ✓82 | ✗ |
| `step`:14 Δ | definition | unc | ✓76 | ?56 | ✗14 | ✗26 | ✗23 | ✗ |
| `continue`:22 Δ | definition | supp | ✓83 | ✗28 | ✓60 | ✓76 | ✓79 | ✗ |
| `identity`:26 Δ | definition | supp | ?41 | ✗36 | ✓68 | ?50 | ?53 | ✗ |
| `run`:29 Δ | definition | lead | ✓71 | ✓62 | ✗25 | ✗28 | ✗19 | ✗ |
| `start`:35 Δ | definition | supp | ✓72 | ✓71 | ✓94 | ✓83 | ✓68 | ✓ |

`research/adaptive-tasks/runtime/frontier.bend`: 34 declarations, 11 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Task`:4 Δ | datatype | lead | ?47 | ✓67 | ✗14 | ?51 | ✗02 | ✗ |
| `State`:6 Δ | datatype | lead | ?57 | ✓75 | ✗21 | ?54 | ✗02 | ✗ |
| `Command`:8 Δ | datatype | supp | ?47 | ✓80 | ✓88 | ✓60 | ✓65 | ✗ |
| `phase`:11 Δ | definition | supp | ✓85 | ✓68 | ✓82 | ✓82 | ✓67 | ✓ |
| `mark`:15 Δ | definition | supp | ✓92 | ✓80 | ✓88 | ✓73 | ✓79 | ✓ |
| `find`:23 Δ | definition | supp | ✓80 | ✓79 | ✓81 | ✓97 | ✓94 | ✓ |
| `append`:31 Δ | definition | supp | ✓95 | ✓76 | ?57 | ✓98 | ✓94 | ✗ |
| `length`:36 Δ | definition | supp | ✓91 | ✓73 | ?55 | ✓94 | ✓83 | ✗ |
| `result`:41 Δ | definition | supp | ✓78 | ✓69 | ✓81 | ✓87 | ?47 | ✗ |
| `offer_space`:45 Δ | definition | supp | ✓69 | ✓67 | ✓90 | ✓65 | ✗31 | ✗ |
| `offer_ready`:51 Δ | definition | supp | ✓75 | ✓80 | ✓95 | ✓83 | ✓82 | ✓ |
| `offer_task`:57 Δ | definition | supp | ✓61 | ✓81 | ✓95 | ✓87 | ✓72 | ✓ |
| `offer`:63 Δ | definition | supp | ?47 | ✓80 | ✓97 | ✓90 | ✓88 | ✗ |
| `wake_ready`:67 Δ | definition | supp | ✓79 | ✓66 | ✓92 | ✓75 | ✓68 | ✓ |
| `wake_task`:72 Δ | definition | supp | ✓74 | ✓73 | ✓93 | ✓83 | ✓77 | ✓ |
| `wake`:77 Δ | definition | supp | ?52 | ✓77 | ✓94 | ✓91 | ✓83 | ✗ |
| `running`:81 Δ | definition | supp | ✓93 | ✓78 | ✓88 | ✓92 | ✓82 | ✓ |
| `admit`:89 Δ | definition | supp | ✓68 | ✓66 | ✓88 | ?44 | ✓75 | ✗ |
| `prepare`:95 Δ | definition | supp | ?49 | ✓79 | ✓96 | ✓82 | ✓72 | ✗ |
| `instruction`:102 Δ | definition | supp | ✓83 | ✓68 | ✓84 | ✓80 | ✓63 | ✓ |
| `advance`:109 Δ | definition | supp | ?48 | ✓72 | ✓85 | ✓72 | ?58 | ✗ |
| `execute_task`:116 Δ | definition | unc | ✓65 | ✓81 | ✗24 | ?42 | ✗07 | ✗ |
| `execute_tasks`:123 Δ | definition | unc | ?59 | ✓80 | ✗20 | ✗27 | ✗05 | ✗ |
| `execute`:128 Δ | definition | lead | ✗35 | ✓81 | ✗33 | ?43 | ✗20 | ✗ |
| `fault`:134 Δ | definition | supp | ✓89 | ✓61 | ?57 | ✗40 | ✓64 | ✗ |
| `finish`:139 Δ | definition | supp | ✓79 | ?58 | ✓64 | ✓77 | ✓75 | ✗ |
| `publish`:144 Δ | definition | supp | ✗40 | ✓64 | ✓88 | ✓64 | ?49 | ✗ |
| `round`:150 Δ | definition | lead | ?47 | ✓85 | ?44 | ?57 | ✗40 | ✗ |
| `run`:153 Δ | definition | lead | ?49 | ✓85 | ?47 | ?53 | ✗33 | ✗ |
| `task_words`:158 Δ | definition | supp | ✓92 | ✓61 | ?54 | ✓93 | ✓61 | ✗ |
| `observation`:162 Δ | definition | supp | ✓61 | ✓75 | ✓80 | ✓90 | ✓72 | ✓ |
| `initial_at`:168 Δ | definition | supp | ✓88 | ✓63 | ✓62 | ✓81 | ✓74 | ✓ |
| `initial`:171 Δ | definition | supp | ✓86 | ✓61 | ?58 | ✓87 | ?54 | ✗ |
| `trace`:174 Δ | definition | unc | ✗34 | ✓79 | ✗34 | ✗33 | ✗12 | ✗ |

`research/adaptive-tasks/runtime/LAWS.bend`: 8 declarations, 7 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `zero_slice`:6 Δ | law | supp | ✓83 | ✓78 | ✓91 | ✓81 | ✓92 | ✓ |
| `offer_full`:14 Δ | law | supp | ✓65 | ✓79 | ✓92 | ✓89 | ✓89 | ✓ |
| `offer_duplicate`:17 Δ | law | supp | ✓69 | ✓77 | ✓90 | ✓86 | ✓84 | ✓ |
| `prepare_reverse`:20 Δ | law | supp | ✓66 | ✓78 | ✓94 | ✓89 | ✓90 | ✓ |
| `round_suspend`:23 Δ | law | supp | ✓64 | ✓63 | ✓86 | ✓73 | ✓68 | ✓ |
| `round_wait`:26 Δ | law | supp | ✓62 | ✓65 | ✓84 | ✓72 | ✓77 | ✓ |
| `unsupported_slot`:30 Δ | law | supp | ✓85 | ✓69 | ✓73 | ✓94 | ✓91 | ✓ |
| `fault_retains`:34 Δ | law | supp | ?58 | ✓68 | ✓88 | ✓74 | ✓75 | ✗ |

`research/adaptive-tasks/runtime/PROOF.bend`: 8 declarations, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.zero_slice`:4 Δ | law_fill | supp | ?47 | ?50 | ✓80 | ✗30 | ✗33 | ✗ |
| `L.offer_full`:5 Δ | law_fill | supp | ?54 | ✓73 | ✓92 | ✓86 | ?51 | ✗ |
| `L.offer_duplicate`:6 Δ | law_fill | supp | ?55 | ✓71 | ✓88 | ✓84 | ?46 | ✗ |
| `L.prepare_reverse`:7 Δ | law_fill | supp | ?55 | ✓76 | ✓90 | ✓78 | ?56 | ✗ |
| `L.round_suspend`:8 Δ | law_fill | supp | ?47 | ✓61 | ✓85 | ✓73 | ✗39 | ✗ |
| `L.round_wait`:9 Δ | law_fill | supp | ✗35 | ?55 | ✓82 | ✓62 | ✗35 | ✗ |
| `L.unsupported_slot`:10 Δ | law_fill | supp | ?57 | ✓60 | ✓79 | ✓79 | ?49 | ✗ |
| `L.fault_retains`:11 Δ | law_fill | supp | ?57 | ✓72 | ✓89 | ✓69 | ?56 | ✗ |

#### Group `data-lifetime`: composition uncertain (memetic ✓95 / anticipation ✓93 / payoff ?46)

`research/data-lifetime/model.bend`: 70 declarations, 32 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Cell`:4 Δ | datatype | lead | ?52 | ✓64 | ✗15 | ✗28 | ✗02 | ✗ |
| `Holder`:7 Δ | datatype | supp | ✓82 | ✓67 | ✓77 | ✓93 | ?43 | ✗ |
| `Heap`:10 Δ | datatype | lead | ✗30 | ?58 | ✗31 | ?59 | ✗01 | ✗ |
| `Store`:16 Δ | datatype | lead | ?43 | ?59 | ?44 | ✗27 | ✗24 | ✗ |
| `Command`:19 Δ | datatype | lead | ?46 | ✓61 | ✓64 | ?51 | ✗26 | ✗ |
| `choose`:30 Δ | definition | supp | ✓97 | ✓66 | ?58 | ✓99 | ✓92 | ✗ |
| `bind`:35 Δ | definition | supp | ✓86 | ✓67 | ✓82 | ✓97 | ✓88 | ✓ |
| `length`:40 Δ | definition | supp | ✓64 | ✓69 | ✓68 | ✓92 | ✓82 | ✓ |
| `at`:45 Δ | definition | supp | ✓78 | ✓66 | ✓82 | ✓94 | ✓78 | ✓ |
| `set`:52 Δ | definition | supp | ✓66 | ✓71 | ✓87 | ✓89 | ✓68 | ✓ |
| `add`:59 Δ | definition | supp | ✓78 | ✓68 | ✓71 | ✓92 | ✓88 | ✓ |
| `maximum`:62 Δ | definition | supp | ✓98 | ✓72 | ?55 | ✓99 | ✓95 | ✗ |
| `member`:65 Δ | definition | supp | ✓88 | ✓66 | ✓65 | ✓97 | ✓88 | ✓ |
| `root`:70 Δ | definition | supp | ?46 | ✓74 | ✓94 | ✓93 | ✓62 | ✗ |
| `omit`:75 Δ | definition | supp | ✓89 | ✓76 | ✓87 | ✓94 | ✓96 | ✓ |
| `omit_all`:82 Δ | definition | supp | ✓86 | ✓70 | ✓80 | ✓94 | ✓93 | ✓ |
| `install`:87 Δ | definition | supp | ✓89 | ✓73 | ✓77 | ✓74 | ✓91 | ✓ |
| `vacant`:92 Δ | definition | supp | ✓87 | ✓75 | ✓88 | ✓98 | ✓98 | ✓ |
| `gather`:98 Δ | definition | supp | ✓71 | ✓66 | ✓89 | ✓64 | ✓89 | ✓ |
| `cell`:106 Δ | definition | supp | ?48 | ✓73 | ✓87 | ✓94 | ✓79 | ✗ |
| `erase`:113 Δ | definition | supp | ✓87 | ✓74 | ✓82 | ✓92 | ✓94 | ✓ |
| `count`:120 Δ | definition | supp | ✓83 | ✓75 | ✓82 | ✓88 | ✓95 | ✓ |
| `payload`:128 Δ | definition | supp | ✓94 | ✓71 | ✓60 | ✓96 | ✓95 | ✓ |
| `words`:132 Δ | definition | supp | ✓95 | ✓76 | ✓83 | ✓83 | ✓96 | ✓ |
| `initial`:137 Δ | definition | supp | ?45 | ✓61 | ✓82 | ✓78 | ✗23 | ✗ |
| `with_roots`:140 Δ | definition | supp | ✓78 | ?57 | ✓80 | ✓94 | ✓95 | ✗ |
| `with_readers`:144 Δ | definition | supp | ✓86 | ?58 | ✓81 | ✓94 | ✓95 | ✗ |
| `charged`:148 Δ | definition | supp | ✓87 | ✓66 | ✓78 | ?51 | ✓91 | ✗ |
| `queued`:152 Δ | definition | supp | ✓85 | ?59 | ✓77 | ✓86 | ✓92 | ✗ |
| `Allocation`:157 Δ | datatype | unc | ?52 | ✓70 | ✗19 | ✗20 | ✗19 | ✗ |
| `allocate`:160 Δ | definition | supp | ✓65 | ?58 | ✓91 | ✓86 | ✓89 | ✗ |
| `free`:171 Δ | definition | supp | ?54 | ?56 | ✓89 | ✓75 | ✓61 | ✗ |
| `retained`:176 Δ | definition | supp | ✓82 | ✓62 | ✓86 | ✓76 | ✓90 | ✓ |
| `acquire`:183 Δ | definition | supp | ?58 | ✓61 | ✓88 | ✓79 | ✓89 | ✗ |
| `acquire_all`:188 Δ | definition | supp | ✓65 | ?58 | ✓89 | ✓78 | ✓86 | ✗ |
| `decremented`:193 Δ | definition | supp | ✓93 | ✓64 | ✓77 | ✓91 | ✓94 | ✓ |
| `data_cell`:197 Δ | definition | supp | ✓94 | ✓64 | ✓65 | ✓80 | ✓83 | ✓ |
| `data_edges`:201 Δ | definition | supp | ✓64 | ✓63 | ✓89 | ✓84 | ✓84 | ✓ |
| `CopyFrame`:208 Δ | datatype | unc | ?56 | ✓62 | ✗21 | ✗15 | ✗13 | ✗ |
| `Copying`:212 Δ | datatype | lead | ?45 | ✓67 | ?47 | ✗26 | ✗11 | ✗ |
| `visits`:215 Δ | definition | supp | ✓93 | ✓83 | ✓79 | ✓91 | ✓91 | ✓ |
| `copying`:220 Δ | definition | supp | ✓73 | ?55 | ✓77 | ✓79 | ?51 | ✗ |
| `assemble`:226 Δ | definition | supp | ✗18 | ✓61 | ✓87 | ✓69 | ?57 | ✗ |
| `enter_copy`:236 Δ | definition | supp | ?49 | ✓66 | ✓92 | ✓79 | ✓68 | ✗ |
| `lookup`:241 Δ | definition | supp | ✓69 | ✓63 | ✓77 | ✓93 | ✓92 | ✓ |
| `copy_step`:245 Δ | definition | lead | ?42 | ✓68 | ✗28 | ✗12 | ✗13 | ✗ |
| `copy_run`:253 Δ | definition | lead | ✗37 | ✓72 | ?47 | ✗29 | ✗14 | ✗ |
| `copy`:259 Δ | definition | unc | ✗35 | ✓73 | ?50 | ✗34 | ✗31 | ✗ |
| `held`:262 Δ | definition | supp | ✓75 | ✓67 | ✓75 | ✓86 | ✓94 | ✓ |
| `constructed`:269 Δ | definition | supp | ✓70 | ✓67 | ✓86 | ✓86 | ✓94 | ✓ |
| `alloc`:277 Δ | definition | unc | ✗39 | ?59 | ✗37 | ?58 | ?45 | ✗ |
| `shared`:285 Δ | definition | supp | ?47 | ✓63 | ✓92 | ✓85 | ✓80 | ✗ |
| `share`:293 Δ | definition | unc | ?56 | ✓69 | ✗26 | ?55 | ?43 | ✗ |
| `transferred`:300 Δ | definition | supp | ✓79 | ✓67 | ✓82 | ✓80 | ✓92 | ✓ |
| `opened`:304 Δ | definition | supp | ?53 | ?58 | ✓92 | ✓62 | ✓79 | ✗ |
| `take_cell`:313 Δ | definition | supp | ?45 | ✓62 | ✓95 | ✓86 | ✓90 | ✗ |
| `take`:319 Δ | definition | unc | ?42 | ✓61 | ✗28 | ?49 | ?42 | ✗ |
| `move`:326 Δ | definition | supp | ✓90 | ✓72 | ✓89 | ✓98 | ✓96 | ✓ |
| `release`:333 Δ | definition | supp | ✓83 | ✓66 | ✓89 | ✓97 | ✓94 | ✓ |
| `dropped`:340 Δ | definition | supp | ✓83 | ✓63 | ✓85 | ✓75 | ✓87 | ✓ |
| `release_cell`:345 Δ | definition | supp | ✓72 | ✓68 | ✓93 | ✓88 | ✓88 | ✓ |
| `clean_step`:353 Δ | definition | supp | ✓60 | ✓62 | ✓95 | ✓81 | ✓90 | ✓ |
| `continue_clean`:359 Δ | definition | supp | ?58 | ✓63 | ✓86 | ✓95 | ✓91 | ✗ |
| `clean`:364 Δ | definition | lead | ✗38 | ?50 | ✗26 | ✗32 | ✗17 | ✗ |
| `pin`:372 Δ | definition | supp | ✓93 | ✓76 | ✓91 | ✓98 | ✓97 | ✓ |
| `ack`:379 Δ | definition | supp | ✓91 | ✓76 | ✓86 | ✓98 | ✓97 | ✓ |
| `commit`:384 Δ | definition | supp | ✓75 | ✓62 | ✓88 | ✓95 | ✓91 | ✓ |
| `step`:389 Δ | definition | lead | ?42 | ✓66 | ?56 | ?47 | ✗22 | ✗ |
| `wrapped`:401 Δ | definition | supp | ?56 | ?49 | ✓79 | ✓93 | ✓80 | ✗ |
| `transition`:405 Δ | definition | unc | ?44 | ?58 | ?57 | ?49 | ✗24 | ✗ |

`research/data-lifetime/observe.bend`: 7 declarations, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `numbers`:4 Δ | definition | supp | ?58 | ✓65 | ✓72 | ✓90 | ✓70 | ✗ |
| `holders`:10 Δ | definition | supp | ?59 | ✓71 | ✓76 | ✓97 | ✓93 | ✗ |
| `cell`:16 Δ | definition | supp | ✓71 | ✓65 | ?57 | ✓96 | ✓84 | ✗ |
| `cells`:20 Δ | definition | supp | ?52 | ✓75 | ✓75 | ✓94 | ✓86 | ✗ |
| `wire`:26 Δ | definition | supp | ✓64 | ✓73 | ✓80 | ✓86 | ✓91 | ✓ |
| `report`:31 Δ | definition | supp | ?53 | ✓60 | ✓82 | ✓93 | ✓84 | ✗ |
| `run`:39 Δ | definition | unc | ?52 | ✓65 | ?43 | ✗40 | ✗19 | ✗ |

`research/data-lifetime/LAWS.bend`: 20 declarations, 6 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rejected_transaction_preserves_state`:4 Δ | law | supp | ✓97 | ✓79 | ✓75 | ✓97 | ✓92 | ✓ |
| `successful_transaction_publishes_state`:9 Δ | law | supp | ✓95 | ✓76 | ✓68 | ✓97 | ✓90 | ✓ |
| `type_is_not_shareable`:14 Δ | law | supp | ✓82 | ✓65 | ✓87 | ✓94 | ✓88 | ✓ |
| `count_ceiling_preserves_state`:19 Δ | law | supp | ✓71 | ?50 | ✓79 | ✓87 | ✓83 | ✗ |
| `copied_leaf_has_distinct_owner`:24 Δ | law | unc | ✓67 | ✓64 | ✗28 | ✓79 | ✓81 | ✗ |
| `counted_leaf_retains_one_record`:29 Δ | law | supp | ✓61 | ?58 | ✓88 | ✓88 | ✓84 | ✗ |
| `empty_capacity_rejects_allocation`:34 Δ | law | supp | ✓78 | ?58 | ✓86 | ✓95 | ✓83 | ✗ |
| `copied_allocation_installs_owner`:39 Δ | law | supp | ✓64 | ?57 | ✓84 | ✓86 | ✓74 | ✗ |
| `counted_allocation_starts_at_one`:44 Δ | law | supp | ✓74 | ✓61 | ✓84 | ✓91 | ✓87 | ✓ |
| `copied_release_keeps_other_value`:49 Δ | law | supp | ?49 | ?50 | ✓86 | ✓79 | ✓61 | ✗ |
| `shared_open_acquires_children`:54 Δ | law | supp | ?59 | ?59 | ✓90 | ✓83 | ✓80 | ✗ |
| `zero_budget_retains_obligation`:59 Δ | law | supp | ✓65 | ✓61 | ✓89 | ✓91 | ✓87 | ✓ |
| `reader_blocks_reuse`:65 Δ | law | supp | ?46 | ?55 | ✓88 | ✓62 | ?51 | ✗ |
| `type_last_release_drops_once`:71 Δ | law | supp | ✓65 | ✓61 | ✓92 | ✓91 | ✓83 | ✓ |
| `data_first_release_keeps_alias`:76 Δ | law | supp | ?51 | ?57 | ✓88 | ✓78 | ✓67 | ✗ |
| `data_last_release_reclaims`:81 Δ | law | supp | ?47 | ✓61 | ✓92 | ✓78 | ✓65 | ✗ |
| `consume_transfers_fields`:86 Δ | law | supp | ?48 | ?59 | ✓89 | ✓79 | ✓72 | ✗ |
| `release_queues_without_disposal`:90 Δ | law | supp | ✓68 | ?57 | ✓88 | ✓85 | ✓84 | ✗ |
| `suspension_moves_one_holder`:95 Δ | law | supp | ✓76 | ?56 | ✓84 | ✓94 | ✓91 | ✗ |
| `immutable_graph_rejects_backpatch`:100 Δ | law | supp | ✓83 | ?55 | ✓84 | ✓91 | ✓87 | ✗ |

`research/data-lifetime/PROOF.bend`: 20 declarations, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.rejected_transaction_preserves_state`:4 Δ | law_fill | supp | ✓88 | ✓66 | ✓85 | ✓81 | ?54 | ✗ |
| `L.successful_transaction_publishes_state`:5 Δ | law_fill | supp | ✓84 | ✓62 | ✓82 | ✓86 | ?42 | ✗ |
| `L.type_is_not_shareable`:6 Δ | law_fill | supp | ?52 | ?43 | ✓86 | ✓84 | ✗37 | ✗ |
| `L.count_ceiling_preserves_state`:7 Δ | law_fill | supp | ✗39 | ?53 | ✓81 | ✓66 | ?43 | ✗ |
| `L.copied_leaf_has_distinct_owner`:8 Δ | law_fill | supp | ✗38 | ✓63 | ✓86 | ✓83 | ?48 | ✗ |
| `L.counted_leaf_retains_one_record`:9 Δ | law_fill | supp | ?49 | ✓65 | ✓86 | ✓76 | ?58 | ✗ |
| `L.empty_capacity_rejects_allocation`:10 Δ | law_fill | supp | ✓61 | ?54 | ✓89 | ✓84 | ?59 | ✗ |
| `L.copied_allocation_installs_owner`:11 Δ | law_fill | supp | ✓65 | ✓64 | ✓86 | ✓79 | ✓62 | ✓ |
| `L.counted_allocation_starts_at_one`:12 Δ | law_fill | supp | ✓62 | ✓61 | ✓86 | ✓87 | ?56 | ✗ |
| `L.copied_release_keeps_other_value`:13 Δ | law_fill | supp | ✗38 | ✓62 | ✓87 | ✓84 | ?46 | ✗ |
| `L.shared_open_acquires_children`:14 Δ | law_fill | supp | ✗34 | ?57 | ✓90 | ✓74 | ?42 | ✗ |
| `L.zero_budget_retains_obligation`:15 Δ | law_fill | supp | ?41 | ✓62 | ✓91 | ✓80 | ?52 | ✗ |
| `L.reader_blocks_reuse`:16 Δ | law_fill | supp | ✗26 | ?51 | ✓78 | ✓72 | ✗24 | ✗ |
| `L.type_last_release_drops_once`:17 Δ | law_fill | supp | ✗32 | ✓60 | ✓84 | ✓77 | ✗38 | ✗ |
| `L.data_first_release_keeps_alias`:18 Δ | law_fill | supp | ✗32 | ?59 | ✓86 | ✓64 | ✗34 | ✗ |
| `L.data_last_release_reclaims`:19 Δ | law_fill | supp | ✗30 | ?57 | ✓87 | ✓77 | ✗35 | ✗ |
| `L.consume_transfers_fields`:20 Δ | law_fill | supp | ✗37 | ?58 | ✓89 | ✓72 | ?53 | ✗ |
| `L.release_queues_without_disposal`:21 Δ | law_fill | supp | ?58 | ✓60 | ✓89 | ✓64 | ?52 | ✗ |
| `L.suspension_moves_one_holder`:22 Δ | law_fill | supp | ✓66 | ✓63 | ✓87 | ✓63 | ?47 | ✗ |
| `L.immutable_graph_rejects_backpatch`:23 Δ | law_fill | supp | ✓70 | ?57 | ✓86 | ✓77 | ✓61 | ✗ |

#### Group `fields-wasm`: composition below_target (memetic ✓75 / anticipation ✓73 / payoff ✗17)

`tests/compiler-fields-wasm/compile.bend`: 4 declarations, 1 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `compile`:8 Δ | definition | supp | ✓65 | ✓64 | ✓81 | ✓96 | ✓86 | ✓ |
| `configured`:13 Δ | definition | supp | ?52 | ?58 | ✓78 | ✓93 | ✓88 | ✗ |
| `arguments`:22 Δ | definition | supp | ?53 | ?57 | ✓82 | ✓96 | ✓88 | ✗ |
| `main`:30 Δ | definition | supp | ?48 | ?41 | ?58 | ✓84 | ✓77 | ✗ |

`tests/compiler-fields-wasm/LAWS.bend`: 5 declarations, 4 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `enum_capability_preserved`:7 Δ | law | supp | ✓87 | ✓79 | ✓91 | ✓100 | ✓87 | ✓ |
| `fields_capability_follows_checking`:11 Δ | law | supp | ✓86 | ✓76 | ✓86 | ✓98 | ✓92 | ✓ |
| `erased_constructor_still_has_a_cell`:15 Δ | law | supp | ✓81 | ?54 | ✓83 | ✓79 | ✓77 | ✗ |
| `erased_argument_takes_no_slot`:22 Δ | law | supp | ✓88 | ✓78 | ✓97 | ✓98 | ✓94 | ✓ |
| `erased_pattern_keeps_offset_and_locals`:38 Δ | law | supp | ✓82 | ✓81 | ✓97 | ✓95 | ✓89 | ✓ |

`tests/compiler-fields-wasm/PROOF.bend`: 5 declarations, 3 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `L.enum_capability_preserved`:5 Δ | law_fill | supp | ✓82 | ✓77 | ✓89 | ✓85 | ✓78 | ✓ |
| `L.fields_capability_follows_checking`:6 Δ | law_fill | supp | ✓86 | ✓70 | ✓80 | ✓85 | ✓86 | ✓ |
| `L.erased_constructor_still_has_a_cell`:7 Δ | law_fill | supp | ✓79 | ✓60 | ✓88 | ✓81 | ?47 | ✗ |
| `L.erased_argument_takes_no_slot`:8 Δ | law_fill | supp | ✓72 | ✓73 | ✓94 | ✓88 | ?58 | ✗ |
| `L.erased_pattern_keeps_offset_and_locals`:9 Δ | law_fill | supp | ✓67 | ✓77 | ✓97 | ✓86 | ✓61 | ✓ |

#### Group `fields-bounds`: composition below_target (memetic ?47 / anticipation ✓68 / payoff ✗2)

`tests/compiler-fields/bounds.bend`: 4 declarations, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `show`:9 Δ | definition | supp | ?51 | ✓66 | ✓90 | ✓85 | ✓80 | ✗ |
| `add`:15 Δ | definition | supp | ?53 | ✓63 | ✓92 | ✓77 | ✓83 | ✗ |
| `text`:19 | definition | supp | ?47 | ✓72 | ✓93 | ✓92 | ✓85 | ✗ |
| `main`:24 | definition | supp | ?50 | ✓66 | ✓94 | ✓87 | ✓76 | ✗ |

#### Group `io-read-bytes`: composition below_target (memetic ✗30 / anticipation ✓63 / payoff ✗25)

`tests/compiler-io-abi-2/read-bytes.bend`: 12 declarations, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `numbers`:6 Δ | definition | supp | ✓93 | ?54 | ?53 | ✓90 | ✓75 | ✗ |
| `scalars`:11 Δ | definition | supp | ✓96 | ✓68 | ?57 | ✓98 | ✓89 | ✗ |
| `decoded`:16 Δ | definition | supp | ✓90 | ?51 | ✓71 | ✓94 | ✓91 | ✗ |
| `shown`:21 Δ | definition | supp | ✓78 | ?49 | ✓66 | ✓92 | ✓84 | ✗ |
| `text`:26 Δ | definition | supp | ✓81 | ?44 | ✓74 | ✓91 | ✓87 | ✗ |
| `read`:30 Δ | definition | lead | ✓70 | ?52 | ✗08 | ✓62 | ✗17 | ✗ |
| `limit`:35 Δ | definition | supp | ?42 | ?52 | ✓80 | ✓91 | ✓77 | ✗ |
| `report`:40 Δ | definition | supp | ?44 | ?42 | ✓75 | ✓84 | ✓72 | ✗ |
| `reads`:46 Δ | definition | lead | ?51 | ?59 | ✗18 | ✗21 | ✗13 | ✗ |
| `opened`:52 Δ | definition | supp | ✗33 | ✓60 | ✓87 | ✓91 | ✓80 | ✗ |
| `arguments`:57 Δ | definition | unc | ✗36 | ✓63 | ✗18 | ✗25 | ✗09 | ✗ |
| `main`:62 Δ | definition | unc | ✗35 | ?48 | ✗12 | ✗22 | ✗07 | ✗ |

#### Group `io-empty-write`: composition below_target (memetic ✗19 / anticipation ?42 / payoff ?48)

`tests/compiler-io/host/empty-write.bend`: 7 declarations, 0 meet all targets

| declaration | kind | role | brain | delight | memetic | anticip. | payoff | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `write_result`:3 Δ | definition | supp | ?56 | ?53 | ✓74 | ✓97 | ✓96 | ✗ |
| `read_result`:8 Δ | definition | supp | ✓66 | ?41 | ?43 | ✓97 | ✓94 | ✗ |
| `read_pair`:13 Δ | definition | supp | ✓70 | ?46 | ✓72 | ✓82 | ✓85 | ✗ |
| `write_pair`:19 Δ | definition | supp | ✗33 | ?56 | ✓89 | ✓81 | ✓83 | ✗ |
| `opened`:26 Δ | definition | unc | ✗30 | ✓76 | ✗17 | ?49 | ✗38 | ✗ |
| `arguments`:31 Δ | definition | lead | ✗29 | ✓79 | ✗22 | ✗34 | ✗35 | ✗ |
| `main`:36 Δ | definition | supp | ✗34 | ✓69 | ✓90 | ✓79 | ✓84 | ✗ |


### Disposition

No rewrite was made and none is proposed from these scores alone: they do not establish a defect, several groups meet the memetic and anticipation targets while missing payoff, and rewriting only to move a judge is excluded by the maintenance procedure. Below-target and uncertain results stand as recorded. Concrete opportunities from the data: (1) the changed declarations of `src/LAWS.bend` and `src/PROOF.bend` (parser-boundary laws and their fills) miss memetic, anticipation and payoff together, the strongest candidate for a reading hypothesis; (2) `wasm.bend` fielded-emission helpers fail memetic, anticipation and payoff (12, 10, 12 below target); (3) the recursion proof entry is uniform `{==}` fills whose payoff is uncertain (7). No evidence-backed disagreement with the judge was found.

### Fixture suites

See [style-fixtures.md](style-fixtures.md). 420 fixture and authored-fixture files, 3,934 declarations, 761 meet all five; suite compositions are available for 9 of 14 suites (`io` meets its composition targets; eight are uncertain or below) and unavailable for five because the group exceeds 48,000 bytes or has unresolved references. Fixtures are deliberate minimal inputs; low memetic scores there are not a reading target.

## Limits and blockers

- The task file `src/SPEC.md` (20,417 bytes) exceeds the 16 KB cap, so Galaxy brain is advisory where it was supplied (FU-2). `io-empty-write` ran with no task (`missing_task_context`); `tests/compiler-io/FIXTURES.md` (18 KB) and the 22 KB and larger fixture documents are over the cap, so those suites ran without a task.
- Suite gates for `tests/compiler-recursion` and `tests/subsets` were not re-run; their fixture judgments rest on seed `--check-only` status and headers. The other eight suites were re-verified read-only (E9).
- Fixture and probe scratch files were created in a scratch worktree and deleted; the toolchain symlink there was unlinked (`unlink`, not `rm -r`). The adaptive-runtime CPU gate wrote only ignored `.local` output.
- The npm wrapper in this shell prints a package-firewall banner and "command failed" on any non-zero Perch exit (findings exit 3); this is not a Perch failure.
- A model verdict is not acceptance. Type, quantity, proof, backend and performance gates remain the deterministic authority.

## Reproduce

```sh
git -C /Users/ericfode/src/knot diff --name-only 185b7d5 a6367eb9 -- '*.bend'
cd /Users/ericfode/src/knot && BEND_NO_TELEMETRY=1 npm run -s lint -- src/scope.bend
cd /Users/ericfode/src/knot && BEND_NO_TELEMETRY=1 npm run -s lint:style -- --live --incremental --manifest=docs/compiler-campaign/manifest.json --group=checking
BEND_NO_TELEMETRY=1 bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts src/recursion-PROOF.bend
```
