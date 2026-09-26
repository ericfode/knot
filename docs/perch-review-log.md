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
