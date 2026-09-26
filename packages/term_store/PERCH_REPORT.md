# TermStore live Perch audit — 2026-09-26

**Complete: no reported production findings and no confirmed production defect.**
All **19 live requests received 19 provider responses**, with **97 rule answers**:
84 Bend-source checks, nine law-packet checks, and four dedicated-rule controls.
Actual model: **jev-1.13.0** (requested `jev-latest`), Perch 0.3.5. No request errors,
zero-coverage results, rate-limit retries, or missing responses were counted as passes.

No Bend source, accepted law, or rule text changed. The complete 14-file upload
closure still matches published `0xce7bfa94c40ded8493cdb39d330add0c`; no republication.
The release-time unavailable-key statements/receipts remain historical evidence;
this report supplies the current live-audit result.

## Coverage and receipts

Every request used `npm run lint -- <path> --rules <names> --json`. The six selected
source rules were `bend-fuel-completeness`, `bend-machine-arithmetic`,
`bend-borrow-lifetime`, `bend-ordered-f32`, `bend-effect-boundary`, and
`bend-device-stack`, each at floor 80%. Every listed source returned all six answers
and zero reported findings. “Arithmetic” below is raw **probability broken**, not a
reported defect. It was the largest source-rule score on every file.

| File | Checks | Arithmetic | Copied wrapper receipt |
| --- | ---: | ---: | --- |
| `LAWS.bend` | 6 | 68% | [`source-LAWS.json`](evidence/perch-audit-2026-09-26/source-LAWS.json) |
| `PROOF.bend` | 6 | 69% | [`source-PROOF.json`](evidence/perch-audit-2026-09-26/source-PROOF.json) |
| `benchmark.bend` | 6 | 62% | [`source-benchmark.json`](evidence/perch-audit-2026-09-26/source-benchmark.json) |
| `checks.bend` | 6 | 59% | [`source-checks.json`](evidence/perch-audit-2026-09-26/source-checks.json) |
| `conformance.bend` | 6 | 60% | [`source-conformance.json`](evidence/perch-audit-2026-09-26/source-conformance.json) |
| `data_checks.bend` | 6 | 63% | [`source-data_checks.json`](evidence/perch-audit-2026-09-26/source-data_checks.json) |
| `example.bend` | 6 | 64% | [`source-example.json`](evidence/perch-audit-2026-09-26/source-example.json) |
| `lifecycle.bend` | 6 | 57% | [`source-lifecycle.json`](evidence/perch-audit-2026-09-26/source-lifecycle.json) |
| `main.bend` | 6 | 60% | [`source-main.json`](evidence/perch-audit-2026-09-26/source-main.json) |
| `memo_checks.bend` | 6 | 61% | [`source-memo_checks.json`](evidence/perch-audit-2026-09-26/source-memo_checks.json) |
| `model.bend` | 6 | 60% | [`source-model.json`](evidence/perch-audit-2026-09-26/source-model.json) |
| `payload.bend` | 6 | 56% | [`source-payload.json`](evidence/perch-audit-2026-09-26/source-payload.json) |
| `release.bend` | 6 | 74% | [`source-release.json`](evidence/perch-audit-2026-09-26/source-release.json) |
| `tests/remote_consumer.bend` | 6 | 68% | [`source-remote_consumer.json`](evidence/perch-audit-2026-09-26/source-remote_consumer.json) |

Exact full source hashes, root `.perch/usage` receipt paths/IDs, commands, selected
rules, actual models, raw scores and provider counts are retained in those receipts
and [manifest.json](evidence/perch-audit-2026-09-26/manifest.json). The `main.bend`
pilot was run live in this audit and reused once. Shared-law configuration changed
between that pilot and the remaining calls; its selected six Bend rules were
unchanged. Each receipt retains its actual global configuration hash.

`LAW_REVIEW.md` received all eight `law-*` rules plus
`term-store-memo-completion-boundary`: **9/9 answers, zero reported findings**.
Largest broken probability: observable essence 57%; dedicated memo rule 10%.
[Law receipt](evidence/perch-audit-2026-09-26/law-review.json).
All nine rules remain advisory at floor 80%. The unrelated source-package
checkpoint rule's calibrated floor **70% was preserved**, not applied to TermStore
or edited. [Configuration identities](evidence/perch-audit-2026-09-26/configuration.json).

Exclusions: `tests/remote_proofs.bend` is a single import of the published proof
entry; both local proof and release entry were checked. The three intentional
checker-negative fixtures (`closure_payload`, `duplicate_store`, `duplicate_memo`)
remain deterministic rejection tests, not expected-clean Perch inputs. `.build/`
contains generated code/binaries, downloaded dependencies, and deliberately mutated
copies; original sources were checked. Host scripts implement orchestration rather
than Bend semantics and are outside the six Bend rules. The generated remote
consumer was nevertheless included because it contains executable consumer logic.

## Dedicated-rule controls and adjudication

Rule text and floor stayed unchanged. Scores are probability broken; floor = 80%.

| Control | Expected | Score | Observed / adjudication |
| --- | --- | ---: | --- |
| clean | clean | 28% | No finding; correct |
| broken | broken | 86% | Finding; **confirmed intentional defect**: exhausted Cancel installs Ready(0) |
| held_out_clean | clean | 26% | No finding; correct: interrupted cell remains incomplete |
| held_out_broken | broken | 88% | Finding; **confirmed intentional defect**: Pending/Evaluating result fabricates success 1 |

Receipts: `control-{clean,broken,held_out_clean,held_out_broken}.json` in the audit
evidence directory. **Zero control misses; zero reported false positives,
duplicates, or unresolved findings.** Both reported findings are intentional control
defects, not production bugs. This four-case separation is preliminary calibration,
not a production-accuracy estimate or grounds to promote the advisory rule.
[Adjudication record](evidence/perch-audit-2026-09-26/adjudication.json).

The repeated below-floor arithmetic signal (56–74%) produced no concrete defect on
source review. `release.bend` scores 74% while containing only imports and an IO
delegation; proof/simple fixture files similarly lack indexing arithmetic. The main
scope increment is guarded at 0xffffffff; allocation uses checked, pinned Vec.
Conformance PRNG wrapping is intentional. List-model/trace sizes are bounded by the
store contract; memo inspection has three cells. The benchmark checks every result
and accumulates failure as False, so unsupported huge workloads cannot masquerade
as successful partial results. The law packet's observable-essence signal is
addressed by exact values/IDs, independent state comparisons, metadata checks and
semantic mutants. These are below-threshold signals, not additional CLI findings;
no correct semantics were changed to reduce them. Shared-rule tuning is left to its
owner; this evidence is available for the shared review log.

## Verification and limits

Current uploaded-file and gate-source hashes match the published release, and every
historical release receipt digest still matches. Therefore the existing zero-hole
proof, CPU/JS conformance, ten type-correct semantic kills, three intended-phase
negative tests, scaling and remote-consumer evidence applies to these exact sources.
No checker/runtime rerun was needed because no Bend source changed.
[Identity verification](evidence/perch-audit-2026-09-26/verification.json).

Added only this report, credential-free audit evidence, and `scripts/perch-audit.py`.
Credentials stayed in the existing Perch configuration; no key was printed or
copied into artifacts. No shared/sibling source was edited;
the required npm wrapper wrote its normal shared usage receipts. Perch has no Bend
AST/call graph; probabilities do not establish semantic completeness, an all-history
store-refinement theorem, concurrent attempt safety, or GPU/Wasm correctness.
