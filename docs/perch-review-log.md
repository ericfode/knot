# Perch review log

## 2026-09-26 — establish usage and maintenance

Scope: current working copy; original nine Bend/compiler rules, eight shared
law rules, and six package rules. Initial survey inspected the package receipts
and STATUS/LAW_REVIEW documents; no source was submitted to a provider.

Evidence:

- [Term-store attempts](../packages/term_store/evidence/perch.json) include
  the review packet and four controls, all stopped by the absent API key.
- [Output-builder coverage](../packages/output_builder/evidence/perch-coverage.json)
  explicitly records zero completed provider requests despite nine matched rules.
- [Symbols attempt](../packages/symbols/receipts/perch-live.json),
  [source attempt](../packages/source/receipts/perch-live.json), and
  [Vec receipt](../packages/vec/receipts/perch.json) record the same blocker.
- [Existing law-gate corrections](LAW-QUALITY-GATE.md) address lossy state
  projections and negative fixtures failing in the wrong checker phase. These
  already have specific rules/regressions; do not add duplicate rules.

Judgment: provider/configuration blocked, **not** low-signal findings. There are
no live probabilities here from which to measure precision. Elapsed wasted time
is unknown. Repeated blocked attempts and the absence of common check history
are observable workflow friction.

Changes: made targeted Perch use part of root AGENTS.md; routed npm checks
through a receipt-writing wrapper; reject zero-coverage checks as non-passes;
record failures separately from findings; skip repeated unchanged credential
failures in the maintenance procedure. Established weekly evidence review with
bounded calibration and a rule-retirement policy. Kept existing thresholds,
contracts, and advisory status intact because there is no model evidence yet
justifying changes to their signal policy.

Validation: the wrapper's offline test exercises real CLI clean/finding paths,
zero coverage, missing credentials and a rejected provider credential. Stubbed
responses test wiring and receipt behavior only. The existing eight-law-rule
wiring/control test remains required. See `npm run lint:verify`.

Next trigger: new development friction, adjudicated findings, or credentials
becoming available for clean/broken/held-out calibration. Do not repeatedly
notify the user of the unchanged missing key.

## 2026-09-26 — credentials and first live calibration

The user supplied a project credential; it was saved privately in ignored `.env`
with owner-only permissions. Doctor passes. This supersedes the current blocker
above without rewriting historical package receipts. No secret is recorded here.

Live controls for `source-checkpoint-observation`, resolved model `jev-1.13.0`:

| Control | Expected | Probability rule is broken | Old floor 80% | New floor 70% |
| --- | --- | --- | --- | --- |
| Clean | pass | 20% | pass | pass |
| Broken | finding | 76% | missed | finding |
| Held-out clean | pass | 19% | pass | pass |

Full input hashes, receipt IDs and observations are in
[the calibration record](perch-calibration/source-checkpoint-2026-09-26.json).
An earlier diagnostic reading of the broken input was 77%; the retained final
comparison was 76%. The check's normal JSON hid these below-floor answers, which
made the false negative look clean. The wrapper now retains raw probabilities,
actual request counts and resolved model IDs from provider responses.

Judgment: one missed synthetic defect; no production precision estimate.
The source package's owner chat was idle with its publication turn completed.
Changed only the rule's reporting floor, 80% to 70%, using separation from both
clean controls; left `gate: false`, wording, package code, and published artifacts
unchanged. This improves recall on observed evidence rather than raising a floor
to hide noise. Replayed retained responses locally to verify pass/finding/pass
without another paid request. The routine review used eight live checks total,
including transport diagnostics and the final recorded three-control comparison.

Next trigger: a fresh held-out broken control and adjudicated real findings before
any gate promotion. Keep other rules advisory pending their own calibration.

Maintenance heartbeat `maintain-knot-perch-rules` is active: Mondays at 09:00
America/Los_Angeles. Unchanged/non-actionable reviews remain quiet.

## 2026-09-26 — adaptive-task proof and review increment

Scope: `research/adaptive-tasks/`, with a live audit of the older abstract join.
The [research report](../research/PERCH_REPORT.md) retains 14 actual provider
responses / 88 rule checks, model `jev-1.13.0`, exact inputs, and adjudication.
No emitted finding required a source change; WGSL/host code remain outside
these Bend/law rules. This is advisory evidence beside deterministic gates.

Development friction: initial U32 syntax, an erased scrutinee used for live
proof case analysis, and a redundant rewrite caused avoidable checker retries.
They were corrected with explicit U32 primitives, an appropriate live affine
law argument, and the direct absorption lemma. No accepted law was weakened.
The nearby valid ownership control and exact quantity diagnostics prevent a
parse failure from masquerading as a successful negative. Elapsed rework time
was not measured.

A manual law review also exposed the weakness of using the implementation's
own tick function as its expected arithmetic. The final one_tick equation
spells out the intended arithmetic independently; a wrong constant typechecks
but fails that law and its runtime witness. The GPU harness checks the entire
frontier suffix outside declared capacity, including capacity 0 and 1.
[The final gate receipt](../research/adaptive-tasks/receipts/checks.json)
records five Bend and three device semantic mutants plus source hashes.

Prevention: start each new protocol with explicit primitive operations, a
complete proof entry, a valid ownership control, and an independent observable
RHS before adding mutation cases. The bounded LAW_REVIEW packet now records
those obligations; existing rules already cover them, so no duplicate rule
was added. Next trigger is a concrete missed defect or noisy finding, not
unchanged reruns of this audit.

## 2026-09-26 — project-wide audit and actual Bend parser

The user requested every owner run Perch and then required the actual `.bend`
parser. [Consolidated report](perch-audit-2026-09-26.md) links all six package
reports, both research areas, exact hashes, live receipts, and exclusions.
The package reports total 115 responses / 580 evaluations; research retains
14 selected responses / 88 evaluations. Avoid double-counting reused parser
smoke receipts. All 88 audited Bend sources and eight real packet hashes were
rechecked against the current files at consolidation.

Confirmed work: IntMap's owner fixed a benchmark accepting zero/out-of-range
input (missed by Perch); root reproduced and fixed a zero-coverage scan passing
in the wrapper after a Perch advisory prompted review. Both have deterministic
regressions. The wrapper also rejects partial parser/provider coverage.
Residual generic wrapper advisories are recorded without inventing a cause.
No package upload source changed and no publication occurred.

Calibration: shared law controls classified 19/24 correctly, missing five known
violations; intended rules also missed two historical regressions. The proof-
claim rule needs a narrower claim/evidence question, not a lower threshold.
Vec's owner repaired two missed stale-length controls with direct wording,
then detected a fresh broken control at 90%; its floor remains 80%. The
OutputBuilder 79% miss and arithmetic-free wrappers scoring around 70–76%
remain evidence for future refinement. Source's calibrated 70% is preserved.
All rules stay advisory. No production accuracy estimate is justified.

Bend is now parsed by vendored, licensed upstream TypeScript parser code at
574b6d39a235b539eb19a5c532993a0abb3d11ad. A version/checksum-guarded Perch adapter
is reapplied by npm postinstall. Syntax parsing, source spans and local graph
edges are deterministic; imported semantic context and complexity metrics
remain explicitly unavailable. No loading/evaluation occurs during parsing.
Ninety-six files / 1,068 definitions and laws parse. Thirteen tests, law wiring,
a fresh isolated npm ci, and live parser-backed file checks passed. Historical
whole-file audit receipts are preserved as such rather than relabeled.

Next maintenance focus: narrow proof-claim integrity against the wrong-phase
regression; calibrate arithmetic-free versus overflowing functions with parsed
context; retain the new coverage guards. Wasted elapsed time is unknown.

## 2026-09-26 — parsed-unit performance checks and Luna 6 repair pilot

The user requested performance checks, a fast-model repair experiment, Luna 6
only, and conversion to appropriate parsed Bend units followed by a full recheck.
[Report](perch-performance-2026-09-26.md) and
[fixed protocol](perch-performance-experiment-protocol.md) retain the evidence.

Confirmed tooling defect: upstream custom method checks supplied an empty helper
graph. Changing only `each: file` to `each: method` would lose the information
needed for complexity review. The adapter now checks exact parsed declarations
with working-copy local helpers, caller/law/datatype context and source hashes.
Named checks remain single-unit; file checks aggregate declarations. Malformed
helpers and partial provider failure reject the run. Context limits remain
visible. All 13 shared source rules are method rules; packet rules remain file
rules. Sixteen offline tests and the law-wiring gate pass.

Four new performance rules remain advisory. Baseline/clean comparisons selected
floors 70/60/60/80; final parsed-unit calibration classified 20/21 correctly with
no clean-control findings. The exact-size-growth held-out source scored exactly
80% and was missed by the strict reporting floor. Retain this miss; do not tune
the floor again to present perfect accuracy. Repeated reads varied, reinforcing
the need for deterministic gates and fresh controls.

Luna 6 passed 1/3 first-shot repairs and 2/3 after one compiler-diagnostic retry.
The rejected candidate invented a list constructor twice. The accepted repairs
preserved complete outputs and reduced measured compiled work at n=1024 from
1,051,656 to 2,055 and from 1,051,655 to 3,080. No parent fixes were credited.
Immutable compilation/output/operation-count gates confirmed all 27 expected
control outcomes. This is finite synthetic evidence, not a cost/speed benchmark
or a universal correctness/complexity proof. Use Luna 6 only for future bounded
repair trials and escalate after one failed diagnostic retry.

The final corpus pass answered 10,680 source questions over 1,068 declarations,
plus 70 questions on eight real law packets, with no findings. Two files have no
executable declarations; 213 units had bounded helper context. Every source hash
still matched at completion. Total run: 147.844 seconds, including the 17 extra
synthetic packets. Those packets produced 34 broad-rule task mismatches and eight
intended owner-rule detections. A targeted owner-only rerun classified 16/17;
OutputBuilder's empty-chunk O(N) claim remains missed. The corpus runner now
selects intended owner rules for synthetic packets to avoid misleading noise.

One corpus pass was interrupted when final adapter edits arrived during the
run. Its receipt is preserved separately, never added to final coverage.
Procedure patch: finish adapter edits/offline gates and freeze the installation
before paid corpus dispatch. No package source or publication changed.

## 2026-09-26 — ordinal style rankings

The user requested separate rankings for conceptual compression and high-dopamine
reading: dense composition, precise vocabulary, symmetry and satisfying insight.
[Rubrics](../perch-style.json), [command and pilot](perch-style.md), and
[raw evidence](perch-calibration/style-2026-09-26.json) define the increment.

Confirmed execution limitation: Perch 0.3.5 can compile a Score question from
configuration, but custom method checks consume only `noul` answers. The opt-in
`lint:rank` companion supplies typed ordinal questions directly while reusing
the pinned Bend parser and bounded working-copy context. It emits independent
rankings and near-tie markers; style never becomes a defect or acceptance gate.
Failure, malformed answers and changed model identity produce no partial ranking.
Receipts include hashes, distributions, model, request coverage and token usage.

Three equivalent-task specimens passed the unchanged compiler/output/scaling
evaluator, with 19 semantic probes each. All five parsed declarations also
received the relevant prefix-copy rule; no findings. Two style runs (six
requests, 12 answers) retained the same order with small score changes. Every
adjacent pair remains a near tie. Judgment quality and agreement with user taste
are unresolved; no strong style preference or productivity gain is established.
Do not retune this rubric just to force a separation in this small cohort.

Twenty-one offline tests and law-rule wiring pass. The maintenance procedure now
separates style preferences from defect precision and requests pre-recorded human
preferences plus held-out examples. Total development effort was not measured.
No package source, accepted law, existing defect rule or repair model changed.

## 2026-09-26 — compiler frontend seed restrictions

The first lexer draft failed repeatedly on actual Bend restrictions: reserved
definition names, computed scrutinees, scrutinee order, and an unannotated local
constructor. The CLI draft also used a local destructure inside `do`, and put an
affine `Result` in a reusable list. These were seed syntax/type failures, not
Perch findings. `src/AGENTS.md` now records the reusable implementation idioms:
parameter helpers, lazy `choose`, `bind`, explicit constructor annotations and
fuel-first recursion. No elapsed-time estimate was reconstructed.

Reference tests exposed two incorrect language assumptions before checking was
implemented: forward live calls are rejected by declaration-event order, and
constructor initializers require a type annotation. The accepted shadowing
fixture now carries that annotation; both rejected forms remain independent
negative fixtures. See [literal cases](../tests/subsets/frontend-cases.json),
[reference diagnostics and gate receipt](../tests/subsets/receipts/frontend.json)
and [law review](../research/compiler-frontend/LAW_REVIEW.md).

Procedure patch: run a representative positive and its nearest negative through
the pinned reference before adding the next surface-language rule. Seed errors
must change the implementation/declared profile, never be relabeled as ownership
evidence. The finished lexer/parser passes both backend lanes and four
type-correct semantic mutation tests; Perch answered 282 targeted checks with
no above-floor findings. Checking and Wasm emission remain outstanding.

## 2026-09-26 — stronger-model repair escalation

The user authorized a smarter model for fixes, superseding the Luna-6-only
restriction. Root instructions and maintenance now select GPT-6 Astra at high
reasoning; Luna 5.6 remains excluded. Historical experiment attribution is
unchanged. The weekly maintenance prompt already reads those instructions and
needs no separate schedule change.

The remaining indexed-list case used its exact original prompt in a fresh
context, with no tools, earlier candidate or evaluator access. Astra's first
attempt also invented `Cons`. Its single compiler-diagnostic retry used the
valid list pattern and passed the unchanged compiler, 19 output probes and six
scaling probes. At n=1024, work dropped from 534,024 to 2,055 operations. No parent
edits were made to either candidate. The accepted source received two parsed-unit
Perch checks with no findings. [Report](perch-performance-2026-09-26.md#stronger-model-escalation)
and [raw results](perch-experiments/2026-09-26-astra-repair/results.json).

Judgment: the original performance defect is confirmed by the independent gate,
and this repair is accepted under that finite JavaScript gate. A stronger model
plus compiler feedback resolved the case Luna left invalid. The constructor
mistake still occurred on the first attempt, so model escalation does not replace
compiler validation. This is one synthetic case; broader productivity, native/GPU
behavior and model superiority remain unestablished. Generation cost and isolated
latency were unavailable. No package source, law, test oracle or threshold changed.

## 2026-09-26 — owner-chat pass and named-unit receipt repair

All nine Knot chats participated in the bounded review or its documentation
applicability decision. [Consolidated report](perch-thread-pass-2026-09-26.md) and
[receipt index](perch-thread-pass-2026-09-26.json) retain 1,499 Bend/law checks in
235 completed provider requests: six packages plus the compiler/checker and
selected earlier parser/task declarations. No source/law findings were reported.
Twenty compiler declaration contexts were truncated. Published package sources
were unchanged. Do not turn this clean count into a precision estimate.

Symbols first identified a confirmed evidence defect: named checks returned their
unit at the top level, but the wrapper saved only file-check `units` arrays.
Source, IntMap and TermStore independently found the same gap. The model had
received the correct context; the historical usage receipt lost its attribution.
Owners retained raw CLI output or supplemental context instead of repeating paid
checks. Normalize both result shapes before recording units. A regression failed
before the fix and passed after it; all 21 offline tests and law-rule wiring pass.
This was inspection-led, not a semantic model discovery. Exact unit/hash retention
belongs in the wrapper contract whenever adding another CLI result shape.

The tooling chat's two additional provider requests emitted a destination advisory
(false-positive for operator-controlled local CLI configuration) and a size
advisory (unresolved; no behavioral defect established). The five offline style
tests passed. Keep both adjudications; no correct-code rewrite or rule-threshold
change was justified. The support survey corrected a stale calibration blocker;
shared documentation now distinguishes the implemented checker from unfinished
evaluation and Wasm emission. No new style ranking was manufactured from unrelated
implementations, and no stronger-model repair was needed.

The compiler owner also reported seed friction during its preceding implementation:
matching catalog/scope metadata before an earlier AST field violated binder order;
flattening expression constructor cases into the outer match fixed it. Passing a
recursive function as a bare callback failed the decreasing-call rule; an explicit
thunk calling on the smaller argument fixed it. Future dispatcher scaffolds should
inspect the expression constructor before later metadata and keep the decreasing
call visible. Existing src/AGENTS.md already requires binder order and structural
fuel; the checker receipts provide concrete examples. No new duplicate rule or
elapsed-time estimate was added. Seven independent semantic mutants, 49 reference
fixtures on two backends and checked helper laws remain the acceptance evidence.

## 2026-09-26 — enum compiler review and arithmetic applicability noise

The first source-to-Wasm increment received 344 checks / 104 completed provider
responses. [Report](../research/compiler-wasm/PERCH_REPORT.md) and
[raw receipt](../research/compiler-wasm/receipts/perch.json) preserve one
false-positive: `bend-machine-arithmetic` scored the constructor-only
`mixed-types.bend::main` at 0.81 broken probability. The complete fixture contains
no arithmetic or conversion; literal upstream/evaluator/Wasm observations agree.
Similar below-floor scores on other constructor-only fixtures expose applicability
noise. No code, oracle or threshold changed. Require a concrete arithmetic path
before acting on this rule; retain these clean controls for future calibration.

The evidence collector initially assumed usage targets included `::name` and
that Markdown packets had parsed units. Both assumptions were wrong: the usage
target is the file, named identity lives in `units`, and the packet has no units.
Match file hash plus parsed-unit identity for Bend and file hash for Markdown;
validate the whole aggregation before writing it. The final receipt has complete
responses and no source/context hash mismatch. No paid checks were repeated.

## 2026-09-26 — assess existing code on all three style axes

User correction exposed a workflow omission: the all-chat defect pass did not run
the style rubrics because ranking required existing alternative implementations.
The actual goal is a quality bar for every declaration. The user refined the
third axis, Highly memetic, to mean a distinctive felt rhythm and conceptual
vocabulary with pull: knowing its words unlocks its ideas and a shared grammar.
Merely memorable or easy to teach was too weak.

The tool now reviews single existing units, files or an explicit project inventory.
All three axes have independent level-3 targets, with normalized mass >=60% meeting
the bar, <=40% below it, and the middle uncertain. All three must meet for an
automatic style pass. Rankings are secondary. Agent and maintenance instructions
require coverage of materially changed declarations without requiring alternatives.
These provisional thresholds were selected before the live run and not adjusted
to manufacture passing results. Semantic acceptance remains deterministic.

[Project report](perch-style-project-2026-09-26.md) retains 5,661 ratings for 1,887
parsed definitions, laws, proof fills and datatypes from 232 discovered files.
The project pass completed 1,872 provider requests and reused 15 matching live
example units; a final 16-unit example reused its results with no paid repeat.
All used jev-1.13.0. Ten syntax-invalid negative fixtures/failed specimens remain
explicitly unranked; an import-only file has no unit. Context was truncated for
308 units. All reviewed source/context hashes matched at consolidation.

Meets-target counts: conceptual compression 1,246; high dopamine 779; memetic 5;
all three 0. These are model judgments, not human preference agreement. The
memetic axis favors several large compiler dispatchers; proof fills and simple
projections score poorly. Investigate role/context sensitivity with human anchors
and held-out examples before treating these judgments as calibrated. Do not
decorate correct proofs, invent jargon, or loosen the floor merely to get passes.
No implementation or accepted law was changed to chase these ratings.

Twenty-five offline tests and law-rule wiring pass, covering single-unit review,
all-axis decisions, full discovery, invalid/empty coverage, concurrency, source
changes and compressed receipt reuse. A separate live review of the changed CLI
retains destination (false-positive), size (unresolved) and ignored-error
(unresolved, not reproduced) advisories. No repair model was needed. Total work
time was not measured; the recorded project evaluation/report phase was 25.890 s.

## 2026-09-26 — style campaign: two improvements, memetic target still unmet

The [first campaign wave](style-campaign/first-wave.md) accepted IntMap's
single-exception branch constructor and OutputBuilder's shared counted join.
Both first candidates passed the unchanged deterministic gates; 20 semantic
mutants were killed by their intended observations. The owners ran 108 semantic
Perch checks without findings and rated 21 declarations on all three axes.
These were style improvements, not repairs of confirmed semantic defects.

All 21 remain below or uncertain on memetic identity. IntMap branch compression
rose 0.61 to 0.92 while delight fell 0.81 to 0.77. OutputBuilder combine's
memetic mass rose 0.04 to 0.32, while attach's delight fell 0.83 to 0.67. These
are distributions from individual judgments, not statistically established
preferences. Reports retain the preregistered author hypotheses, fixed inputs,
full outputs and two capped datatype contexts. No human taste labels were
invented and no threshold changed.

Prevention: preserve a concrete reading hypothesis before each candidate and
keep per-axis regressions visible. Reserve fresh examples for a later test of
small-helper and context sensitivity. Do not repeatedly score the same source,
decorate canonical helpers, or equate successful refactoring with memetic
acceptance. The campaign's rolling inventory invalidates old source/helper
identities and records unrated new declarations without paid rescans.

## 2026-09-26 — Vec: compression improved while delight became uncertain

[Vec growth](style-campaign/vec-growth-1.md), commit `cd78dba`, made the
continuation cases explicit with joint matches. Its first candidate passed
unchanged proof, native/JS, ownership, mutation and native scaling gates.
The 107 frozen inputs and all 12 actual style request/context identities match.
Semantic Perch completed 29 checks without findings; all 12 style units remain
below or uncertain on memetic identity.

The planner's compression target mass rose 0.78 to 0.90 while delight fell
0.61 to 0.52, crossing into uncertainty. Its shared catch-all hides the names
of two stopping cases. Push delight also fell, 0.77 to 0.69, while remaining
above the provisional bar. The author retained the transitions for a concrete
reading benefit, with these costs explicit. This is evidence of distinct axes
and a review tradeoff, not evidence that either the reader or judge is wrong.

Do not make flattening a mechanical style rule or infer a psychological effect
from one model judgment. The next Source search batch must preserve explicit
terminal-state meaning and evaluate its own reading hypothesis before judgment.
No rubric or threshold changed, and no repeat inference was used to hunt for
a preferred result. Broader applicability/calibration questions remain open.


## 2026-09-26 — Owning-store seed constraints and reproducible fixtures

The owning-store draft repeated avoidable seed errors: Base already reserves
Key/Event, computed pair destructuring needs a helper parameter, and a live body
cannot call a later unfilled definition. The [source workflow](../src/AGENTS.md)
now records the name and declaration-order constraints explicitly. Check the
pinned Base namespace before writing a family; order the result helper before
its caller and pass the continuation rather than introducing a forward call.

The [retained first store harness](../research/owned-store/receipts/attempt-001.json.gz)
hit Bun's stack while constructing one 3,531-case input literal. Batching fixed
inputs into 32-case declarations passed both native and Bun without changing
runtime code or expected observations. A later extra witness brought the corpus
to 3,532. This was a harness/backend-boundary failure, not a semantic mutant kill.

Parent review also found that the scope style runner required an ignored source
copy from the current session. It now reconstructs the frozen source closure
from the preregistered Git commit and checks every hash. The [reproduction](../research/compiler-style/family-1/behavior-receipts/attempt-003.json)
passes all 28 observations with unchanged candidate, fixture and oracle. Future
qualification runners must recover their inputs from tracked objects before
claiming a reproducible gate. No model retry or time estimate is inferred from
these harness corrections; no rule/rubric threshold changed.

## 2026-09-26 — Source: a clean review missed a false parameter-boundary claim

The [Source search campaign](../packages/source/STYLE_CAMPAIGN.md), commit
`7bfae7e`, retains the first new law packet and its eight-rule clean review.
Local review caught its claim that locate rejects a foreign ID: `Source.locate`
takes a position, not a cursor, so that claim is inapplicable. The corrected
packet passed one targeted review. No implementation, contract or independent
assertion changed. Final coverage is 18 checks; total usage including the
retained first packet is 26 checks, three requests/responses.

Prevention: trace each packet claim to the exact signature and observation
before submitting it. Reusing a cursor-oriented matrix row for a position-only
operation creates false confidence even when the model returns no findings.
This is a concrete review miss, not evidence for lowering a rule threshold.
Any new automatic rule needs clean/broken/held-out controls before promotion.

Search delight improved 0.57 to 0.65, but compression remains uncertain and
memetic identity below target. Neighbour decreases and the capped datatype
context remain visible. Unlike Vec's planner, this flattening preserves named
terminal states; the two outcomes support separate reading judgments rather
than a blanket flattening rule.

## 2026-09-27 — Symbols balanced identity: policy transition and adverse-input review

The [owner handoff](style-campaign/symbols-identity-v3-2026-09-27.json) verifies
commit `a5345e8`, the selected source and all 23 current v3 source/context
identities. The coordinator recomputed the saved style assessments without new
provider requests. Owner proof, backend, mutation and performance receipts were
inspected, not rerun. Original independent Bend inputs remain unchanged.

After 24 candidates, the balanced prefix trie gives `Trie.get` a current memetic
pass and Anticipation/Payoff masses of 0.64/0.79. Galaxy-brain mass remains zero;
complete v3 coverage is 0/23. Its earlier v2 three-axis pass remains historical.
The owner accepted common-prefix runtime ratios of 0.244–0.568 alongside a
1.54–1.61x cost for 2,048 sorted single-character names. The earlier unbalanced
trie was rejected after adversarial ordering exposed a sibling-chain regression.
Prevention: retain adverse prefix/order families and structural invariant
controls before accepting a pleasing representation. This is an unpublished
implementation improvement, not completion of the broader style pilot.

## 2026-09-26 — Whole-repository throughput and provider saturation

The [throughput report](perch-throughput-2026-09-26.md) confirms repeated Git
discovery, serial declaration checks, batch barriers and repeated context
parsing as avoidable local costs. Exact full-repository request/result controls
retain 1,941 semantic declarations and 2,337 style units. Sixteen workers
completed live semantic/style trials in 39.43/19.78 s versus 70.57/39.19 s.
The original 16 parser failures remain visible; no acceptance rule was relaxed.

The 32/128 semantic and 32/64 style trials overloaded the provider. Retain
their failed coverage as saturation evidence, not speedup claims. Prevention:
bound nested requests as well as top-level workers, choose defaults from
completed coverage, and preserve failed trials when tuning. The shipped default
is 16; eight reduces pressure when sharing provider capacity. All 46 tooling
tests and the law-rule wiring gate pass against merged v3 policy.

A final live check at merged revision `698d88a` received HTTP 402 on its first
request. No further paid checks were attempted. Earlier complete measurements
remain frozen evidence; the merged revision has no complete new live receipt.

After the user purchased credits, [the deferred live checks completed](perch-throughput-2026-09-26.md#live-verification-after-credits-were-added)
at `deddae2`: semantic scan 40.21 s across 1,986 declarations with zero failed
requests; style 22.00 s with all 2,345 parsable units rated. The scan recovered
152 rate-limit responses. The same 16 parser failures still prevent complete
repository coverage. Full results are retained; model findings are untriaged.
No implementation, rule, rubric, or concurrency change was needed.

## 2026-09-26 — Incremental review must invalidate dependencies and question names

The [incremental review audit](perch-incremental-2026-09-26.md) found that
`--since` narrows paths without reconsidering unchanged dependent callers.
An unnamed question hash also allowed an otherwise identical renamed rule to
inherit the old name's answer, and deleted file units or failed rereads could
leave stale results. Focused fixtures reproduced these cases; corrected request
identities and current-unit retention now reject them. Incremental mode validates
the full selected graph and reuses only matching requests.

Prevention: test cache invalidation with changed helpers, renamed questions,
deleted units and failed rereads, not only an unchanged second invocation.
Count carried applicable answers separately from provider calls. The full
offline inventory retains the existing 16 parser failures with zero warm
requests; cache speed is not acceptance evidence or a fresh model judgment.

## 2026-09-26 — Scoped run pilot: deterministic evidence, no style response

The [one-declaration pilot](../research/adaptive-tasks/style-pilot/adaptive-run-1/README.md)
expresses a fueled Checkpoint as the sole progressing case and preserves the
complete owner in its complement. Its first candidate passes twelve unchanged
laws, both intended quantity negatives, native/JS observations, five semantic
mutants and 42 full-state/step-count comparisons. Emitted JavaScript removes a
terminal wrapper reconstruction; that does not establish a style target.

The [live review](../research/adaptive-tasks/style-pilot/adaptive-run-1/style-provider-failure.json)
made one request with zero responses after a transport failure. All three
after-ratings and semantic source/law review remain unavailable. The compiler
owner later reported a working provider in its session, but the bounded review
handoff was blocked by the app's approval policy and was not delivered. Do not
infer a missing key or a global outage. Keep the exact candidate and rubric
frozen; resume targeted review only with changed access, without score chasing.
The current CPU gate reconstructs its frozen inputs from tracked Git objects
and snapshots; it does not require an earlier session's ignored source copy.

After the user changed access, one single-file Git stage succeeded, but staging
the full checkpoint failed at `.git/index.lock` with `Operation not permitted`.
One resumed style request
on the identical source/context/rubric still failed with zero responses; provider
DNS reports `ENOTFOUND`. The app handoff and heartbeat update still return
`approval policy is never`. [Both attempts and the access diagnostic](../research/adaptive-tasks/style-pilot/adaptive-run-1/access-2.json)
remain recorded. No unavailable result became a pass and no candidate changed.

## 2026-09-26 — Flat-store: aliased observations and arithmetic review noise

The compiler owner's [law review](../research/flat-store/LAW_REVIEW.md) records
an aliased Buffer in the first reinitialization comparison. The historical
receipt is retained and disqualified for that claim. Frozen typed-array copies
and a type-correct write-on-reinit mutant now distinguish an unexpected memory
write. This defect was found by direct review before Perch, not by Perch.
Prevention: snapshot bytes independently before the operation, then require a
mutant that writes on the rejected path to fail the preserved observation.

The owner's [Perch report](../research/flat-store/PERCH_REPORT.md) also retains
below-floor arithmetic probabilities of 0.73 for the constant-string
`probes.bend::layout_error` renderer and 0.69 for a locator-law fill. No arithmetic
defect is demonstrated and no code or threshold changed. These are bounded
calibration observations; any future rule revision still needs clean, broken
and held-out controls. The 106-declaration style review has zero all-three
passes and twenty capped helper contexts; it does not satisfy the separate pilot.

## 2026-09-26 — Worktree takeover and repeated proof-claim miss

The takeover worktree lacked ignored dependencies and `.env`. Pinned `npm ci`
installed the Bend adapter, and the existing project credential was copied
privately with mode 0600. Doctor, 28 offline tests and eight-law wiring pass.
The [configuration receipt](perch-calibration/takeover-2026-09-27/README.md)
records 27 custom rules, current provider responses and exact source identities.
Prevent repeated setup confusion by treating installation and credentials as
per-worktree state; doctor alone is not a live provider test.

The unchanged wrong-checker-phase regression still escapes
`law-proof-claim-integrity`: probability broken 0.19 at its 0.80 floor. Offline
inspection confirms the actual packet and intended rule were sent. This repeats
the earlier [0.20 miss](perch-audit-2026-09-26.md), not a new implementation defect
or a reason to lower the floor. `law-mutation-sensitivity` reports the same
synthetic packet at 0.89 and exits 3; that does not repair the intended rule's
false negative. Keep both results and the independent checker-phase gate.

The frozen adaptive runner's first successful style review is 0.82/0.81/0.52
target mass, versus 0.84/0.83/0.57 before. The last axis remains uncertain;
differences this small do not establish a preference. The experiment is retained
and rejected as an all-three success. No candidate, assertion, rubric or
threshold changed, and its successful rating was reused by identity rather than
requested again.

## 2026-09-26 — Galaxy brain extends conceptual compression

The user requested **Galaxy brain** above the existing big-brain scale.
[Level 5](../perch-style.json) rewards a reframing that unifies apparently
essential distinctions and reveals further traceable connections. Level 4
continues to reward an unusually economical solution. The target remains at
least 60% probability on level 3 or higher; the other two axes are unchanged.

The scorer already uses each dimension's own level count. Test fixtures assumed
equal lengths; they now follow each rubric, and the request/receipt integration
check exercises a level-5 answer and its contribution to target probability.
`npm run lint:rules -- --json` and `npm run lint:verify` pass: 28 offline tests
and the eight-law wiring gate. These checks establish wiring, not taste
calibration. No live style ratings were requested. Human calibration of the new
level remains pending; earlier receipts keep their original rubric identity.

## 2026-09-26 Pacific — paired Life inducer experiment

Two fresh Astra/max authors received the same frozen Life contract and current
rubric; one read the selected decoded inducer. Both pass independent behavior
gates. Jev 1.13.0 rates all three axes above target on 6/13 unexposed declarations
and 5/7 exposed declarations. Neither implementation passes the all-declaration
policy. Both public step definitions have memetic target mass 0.88; helper
ratings account for most of the fraction difference. Local context was not
truncated; builtin/unresolved references remain explicit.

This is a calibration question about the unit of judgment, not a confirmed
judge defect or evidence that exposure caused an improvement. Conventional
adapters coexist with a distinctive interacting mechanism. Before changing
that policy, collect human preferences on fresh whole-family and helper
examples; do not tune against these two submissions. All targets and rubrics
remain unchanged. [Protocol, sources, per-declaration distributions and
dispositions](../research/life-blueberry/README.md) preserve the experiment.

## 2026-09-26 Pacific — ten-round Life continuation

The same two authors received their own feedback and up to ten revisions under
unchanged rules and independent assertions. The exposed arm first met all style
targets in round 6 (4/4 declarations); the unexposed arm exhausted ten rounds
with 4/5 meeting every target. Both selected sources pass behavior and source
semantic checks; the final law packet completes eight checks without findings.
[The full history](../research/life-blueberry/iteration/README.md) retains every
snapshot, failed compiler attempt, hypothesis, distribution and disposition.

This does not establish a causal inducer effect or a confirmed judge defect.
The exposed selection's narrowest target mass is 0.61; the unexposed selection's
remaining memetic judgment is 0.56. Its unchanged row.duplex source received 0.59
in round 7: reconstructed request states differ only in the caller's line/end
line positions. That small movement did not change the uncertain category.
Do not attribute it to improved reading or to line positions rather than model
variation. Fresh human judgments and context/reuse calibration would be more
informative than more unchanged requests. No rubric or threshold was adjusted.

An HTTP 402 interrupted round 9 before any provider response. The frozen round
runner then parsed absent JSON and recorded `substring not found`, obscuring
the billing cause in its summary. Retained stderr identified the failure; calls
stopped until the user replenished credits. The recovery kept the same source
and deterministic receipt and wrote new review receipts. Future harnesses should
classify non-success exits and provider failures before parsing JSON, preserving
the original diagnostic and partial usage. The frozen runner was not modified.
