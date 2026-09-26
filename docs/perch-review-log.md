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
