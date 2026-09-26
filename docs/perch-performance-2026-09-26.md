# Parsed Bend checks and Luna 6 repair pilot

Four advisory performance rules now review parsed declarations: growing prefix
copying, repeated invariant summaries, sequential linked-list indexing, and
amortized storage growth. All shared Bend/compiler source rules also use parsed
declarations. Markdown law evidence is still reviewed as a packet.

## Review units and context

`npm run lint -- file.bend` checks each applicable parsed `def` or law declaration.
`npm run lint -- file.bend::name --rules rule-name` selects one. The actual pinned
Bend 2.0.29 parser provides byte spans, names, references, laws, and datatypes.
The adapter supplies current local callees, direct callers, relative imported
helpers, matching laws and datatype context, with source hashes. It refuses
malformed helpers before contacting Perch. Aggregate results retain every
unit's questions, scores, source locations, and context limits.

No remote import or dynamic dispatch is resolved. Context is bounded to 16
helpers, four callers, 12 files and 48 KB, with explicit truncation and unresolved
reference markers. The target declaration is complete. Types/proofs are not
checked by this parser adapter. Data-only and imports-only files have no method
coverage and are reported separately.

## Performance calibration

The original file-based experiment at an 80% floor classified 10/15 controls:
three of eight violations found, seven clean controls passed. Baseline/clean
separation justified advisory floors of 70% for prefix copying, 60% for invariant
work and indexing, and 80% for capacity growth. No rule was promoted to a gate.

After conversion to parsed declarations with helper context, the initial
declaration run classified 15/15 original controls and 6/6 fresh held-out controls.
Those scores cannot isolate the effects of context, wording, and threshold
changes. Held-out means unseen before that run; later repeats are not new
holdouts. All expected labels have independent semantic/performance evidence.
The final installed-version recheck is recorded separately below.

- [Original file calibration](perch-calibration/performance-2026-09-26.json)
- [Initial parsed-unit calibration](perch-calibration/performance-units-2026-09-26.json)
- [Fresh controls](perch-calibration/performance-fresh-units-2026-09-26.json)
- [Deterministic controls](../tests/perch-performance/evidence/controls.json)

## Luna 6 results

Luna 6 at low reasoning received one original source, its public contract and
smoke examples, and a real Perch finding. Agents had no tools or evaluator access.
Candidates were saved unchanged. Compiler failures received at most one retry
containing only the diagnostic, with the same contract and immutable gates.

| Case | First attempt | One diagnostic retry | Work at n=1024, original → accepted |
| --- | --- | --- | ---: |
| Growing prefix copy | Pass | Unneeded | 1,051,656 → 2,055 |
| Repeated invariant summary | Quantity error: reused `s` without `+` | Pass | 1,051,655 → 3,080 |
| Indexed linked list | Invented `Cons` constructor | Still invalid `List.Cons` | 534,024 → no accepted repair |

**One-shot: 1/3. After at most one diagnostic retry: 2/3.** The two accepted
repairs pass type checking, 19 independent full-output probes, and six measured
scaling probes. Their work falls by about 512× and 341× at n=1024. These are
instrumented-operation reductions, not measured wall-clock speedups. Both also
pass the subsequent parsed-unit Perch checks; that model verdict is secondary
to the deterministic gates.

The harness instruments function entries, loops, and object/array allocations
in the actual compiled JavaScript. No candidate-supplied counters or flaky timing
thresholds are used. Frozen gate hash:
`be943077833ee612b6f8ac9b56bc5fdb1af66971c04830b07976e8ca312a6fbb`.
Nine inefficient controls fail work, nine linear controls pass, and nine semantic
mutant runs fail full-output comparisons: 27/27 expected control outcomes.

This is a tiny synthetic feasibility pilot. It does not establish native/GPU
behavior, universal complexity/equivalence, a model ranking, or an improvement
over unaided repair. There was no randomized no-Perch arm. Parameter counts,
separate response model IDs, inference latency, token usage and dollar cost were
not exposed by the agent runner, so no speed/cost claims are made. The standalone
CLI rejected the model name with its ChatGPT authentication; the app runner
accepted the requested Luna 6 setting. Two Luna 5.6 generations finished before
the user's correction; they were excluded, and no further Luna 5.6 work ran.

Use Luna 6 as a bounded patch proposer with a deterministic compiler/test loop.
Give it the public contract and a confirmed finding, allow one diagnostic retry,
then escalate remaining failures. Do not let a clean Perch response authorize a
broken program or weaken the original acceptance gate.

- [Frozen protocol and correction log](perch-performance-experiment-protocol.md)
- [Prompts and model outputs](perch-experiments/2026-09-26-fast-repair/manifest.json)
- [Per-attempt results and diagnostics](perch-experiments/2026-09-26-fast-repair/results.json)
- [Reproducible evaluator](../tests/perch-performance/README.md)

## Final project recheck

The final run used installed profile
`language-pack-1.20-v3+knot-bend-0cd9e831fc413760` and resolved model
`jev-1.13.0`. It finished in 147.844 seconds, with 1,093/1,093 completed provider
responses and 10,903 answered questions. Every primary and context-source hash
still matched after completion. [Full receipt](perch-calibration/bend-units-2026-09-26.json).

| Scope | Bend files | Parsed units | Source-rule checks |
| --- | ---: | ---: | ---: |
| IntMap | 11 | 123 | 1,230 |
| OutputBuilder | 13 | 118 | 1,180 |
| Source | 13 | 238 | 2,380 |
| Symbols | 12 | 91 | 910 |
| TermStore | 18 | 221 | 2,210 |
| Vec | 15 | 176 | 1,760 |
| Adaptive tasks | 10 | 56 | 560 |
| Execution models | 4 | 45 | 450 |
| **Total** | **96** | **1,068** | **10,680** |

No source-rule findings were reported. Eight production law packets received
another 70 checks and no findings. Seven intentionally ill-typed fixtures are
included in the source inventory; their lack of lint findings does not make them
valid programs. Deterministic typing remains necessary.

Two files contain no executable declarations: `packages/source/types.bend`
(datatypes only) and `packages/term_store/tests/remote_proofs.bend` (imports only).
They parsed, but are **not** counted as successful lint coverage. Of the checked
units, 213 reached a helper/context limit. Their focal declaration was complete;
their dependency context was not. Three provisional compiler rules have no
production source yet; their selection was verified in an offline fixture.

The broad run also reviewed 17 synthetic package law packets: 153 questions and
42 findings. Eight findings were from intended owner rules; 34 were from shared
law rules applied to deliberately narrow calibration packets. These are not
production defects. Judge those controls against their intended rule, not every
rule matching the Markdown filename. The owner-rule outcomes were 16/17, missing
the OutputBuilder cost claim that omits arbitrarily many empty chunks.
A separate [owner-rule-only rerun](perch-calibration/package-owner-controls-2026-09-26.json)
confirmed 16/17 with the same miss and no clean-control findings. The reusable
corpus runner now selects intended owner rules for these synthetic packets.

Final installed-version performance calibration was **20/21**: 10/11 violations
detected, 10/10 clean controls passed. The exact-size growth held-out example
scored exactly 80%, which does not exceed its 80% floor. This boundary miss is
retained; the floor was not adjusted again. The two accepted Luna 6 repairs still
passed their targeted parsed-unit rechecks.

- [Final original performance controls](perch-calibration/performance-units-final-2026-09-26.json)
- [Final fresh performance controls](perch-calibration/performance-fresh-units-final-2026-09-26.json)
- [Final accepted-repair rechecks](perch-calibration/performance-repaired-units-final-2026-09-26.json)

Verification: 16 offline parser, context, wrapper, and rule-selection tests pass,
as does the separate eight-law-rule wiring gate. The adapter installation is
idempotent and restored by `npm ci`. No package implementation or release changed.

An earlier paid recheck was interrupted when the adapter was finalized during
execution. Its separate receipt is retained as incomplete, not added to final
coverage. Future corpus runs must freeze the installed adapter and rules before
dispatch; targeted checks are the default for ordinary changes.
