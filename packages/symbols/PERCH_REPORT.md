# Symbols live Perch report — 2026-09-26

Completed **84 relevant checks in 16 live requests/responses**, all using requested
`jev-latest`, resolved **`jev-1.13.0`**, Perch 0.3.5. No production-source or
real-law-packet finding crossed the reporting floor. Both deliberately broken
controls were correctly flagged; the clean control was unflagged. No confirmed
package defect, semantics edit, law change, rule change, or republication.

The release remains `0xf5507d46d06a1a8043dcb1a582194615`: every local upload file
still matches its release SHA-256. Added only this report, an audit driver, and
audit receipts. Historical release documents saying live calibration was
unavailable describe the earlier release checkpoint; this report adds live
evidence without rewriting those receipts.

## Coverage and provenance

All commands used `npm run lint -- <file> --rules <names> --json`. Each retained
receipt records source SHA-256, global rule-set identity, exact selected rules,
all raw probabilities, actual model, provider counts, timing and token usage.
[Full index](receipts/perch-audit-2026-09-26/index.json) maps copies here to the
original `.perch/usage/` receipts. [Verification](receipts/perch-audit-2026-09-26/verification.json)
records receipt hashes, individual rule-file hashes and release/gate comparisons.
No provider failure, retry, zero-coverage check or missing response occurred.

Every Bend file below received all six rules: `bend-fuel-completeness`,
`bend-machine-arithmetic`, `bend-borrow-lifetime`, `bend-ordered-f32`,
`bend-effect-boundary`, `bend-device-stack`. Floors remain 80%, advisory.
The largest below-floor broken score was machine-arithmetic in every file:

| File | Checks | Highest broken score | Receipt |
| --- | ---: | ---: | --- |
| `LAWS.bend` | 6 | 61% | [56b33c5e](receipts/perch-audit-2026-09-26/LAWS_bend-56b33c5e-2110-4ba9-ad84-e7ddd8761029.json) |
| `PROOF.bend` | 6 | 71% | [3c4474f6](receipts/perch-audit-2026-09-26/PROOF_bend-3c4474f6-7430-489b-84da-73d1c6ef7bc8.json) |
| `benchmark.bend` | 6 | 61% | [64f08507](receipts/perch-audit-2026-09-26/benchmark_bend-64f08507-0601-458f-bfb5-b75a662cfe73.json) |
| `cases.bend` | 6 | 57% | [e0822979](receipts/perch-audit-2026-09-26/cases_bend-e0822979-2d36-4186-9438-6570cf7517bf.json) |
| `conformance.bend` | 6 | 73% | [8abd096c](receipts/perch-audit-2026-09-26/conformance_bend-8abd096c-357c-4819-bc08-3f430ec46fe9.json) |
| `example.bend` | 6 | 62% | [5388bdcf](receipts/perch-audit-2026-09-26/example_bend-5388bdcf-94c1-4147-939d-755d978ecdb0.json) |
| `main.bend` | 6 | 59% | [c6555332](receipts/perch-audit-2026-09-26/main_bend-c6555332-efd9-48d4-89eb-c35eeeaa7a9f.json) |
| `model.bend` | 6 | 55% | [8e1bb97c](receipts/perch-audit-2026-09-26/model_bend-8e1bb97c-183a-4272-a050-9f5185677d27.json) |
| `observe.bend` | 6 | 59% | [e72847ea](receipts/perch-audit-2026-09-26/observe_bend-e72847ea-aa2d-40e7-9d9b-7dffe003d125.json) |
| `protocol.bend` | 6 | 66% | [894e968e](receipts/perch-audit-2026-09-26/protocol_bend-894e968e-3e6c-46d0-978a-c7df8de6a45a.json) |
| `release.bend` | 6 | 75% | [e6574a59](receipts/perch-audit-2026-09-26/release_bend-e6574a59-0dd4-450a-a9b4-7ed1d61ad09e.json) |
| `tests/remote_consumer.bend` | 6 | 59% | [b6719124](receipts/perch-audit-2026-09-26/remote_consumer_bend-b6719124-0fc4-4b5d-b405-5b447808f0c9.json) |

This includes the trivial proof/conformance/release entry wrappers and the
remote consumer, so no maintained Bend source was omitted. Excluded `build/`:
generated benchmark entries/binaries/C/JS, fresh-cache copies of the already
covered release and separately owned Vec dependency, and generated mutant copies
with intentionally broken semantics. Host Python/JS orchestration and Markdown
other than the specified law/control packets are outside these Bend file rules.

The real [LAW_REVIEW.md receipt](receipts/perch-audit-2026-09-26/LAW_REVIEW_md-12503000-cda6-45da-aee2-fb5abef95be2.json) has nine checks:
all eight `law-*` rules plus `symbols-bidirectional-preservation`, one complete
provider response. Broken scores (not pass confidence): domain-inhabited 42%; observable-essence 56%; public-contract-coverage 26%; independent-model 24%; state-composition 17%; boundaries-and-exhaustion 26%; mutation-sensitivity 23%; proof-claim-integrity 35%; symbols-bidirectional-preservation 15%.
None reaches the 80% floor. The 70% floor recorded in the supplied Source
calibration applies to `source-checkpoint-observation`, not to Symbols or the
six Bend rules; that configuration was neither selected nor changed here.

## Findings, controls and adjudication

The only two reported findings are **confirmed intentional control defects**:

| Control | Rule true | Rule broken | Outcome | Receipt |
| --- | ---: | ---: | --- | --- |
| `clean.md` | 79% | 21% | unflagged (exit 0) | [24a85340](receipts/perch-audit-2026-09-26/clean_md-24a85340-8834-4af6-b1f6-8edfd7bb57a3.json) |
| `broken.md` | 5% | 95% | flagged (exit 3) | [74bb72df](receipts/perch-audit-2026-09-26/broken_md-74bb72df-21cb-4aa1-aed7-48ce05c83588.json) |
| `held_out.md` | 9% | 91% | flagged (exit 3) | [facb4368](receipts/perch-audit-2026-09-26/held_out_md-facb4368-e2af-4461-b000-d57943175682.json) |

- `broken.md` clears the forward map on failed insertion while retaining reverse
  contents. Re-interning the existing "a" incorrectly reports Exhausted. This is
  the already tested `failure_forgets` semantic mutant in [mutations.json](receipts/mutations.json).
- `held_out.md` constructs a fresh forward map when appending "prefixY", losing
  "prefix" and "prefixX". Re-interning "prefixX" incorrectly allocates a new ID.
  This is the independent example of the tested `forget_forward` defect family.
- The clean control preserves both maps and explicitly observes prior forward
  and reverse results. Its 21% broken score is correctly below the floor.

There are **zero misses and zero false alarms among these three controls**.
These were the first live runs of the existing controls in this audit. This
small, deliberately explicit packet sample is not a general accuracy estimate.
No refinement was warranted: clean/broken separation is 74 percentage points,
clean/held-out separation 70 points. The dedicated rule remains advisory at 80%.

Below-floor scores were read rather than discarded. `bend-machine-arithmetic`
assigns 55–75% broken across all sources, including arithmetic-free
`release.bend` (75%), `conformance.bend` (73%) and `PROOF.bend` (71%). Inspection
finds no concrete arithmetic path in those wrappers. Main delegates checked
bounds/length/push to pinned Vec; its cap is 16,777,216. The model starts search
at zero and cannot grow beyond that cap; the observer counts exactly the table
length. Benchmark calls are bounded to 512 names and 16 repetitions. No supported
path to U32 wrapping was established. These are unreported low-specificity
scores, not confirmed findings or counted false positives. No threshold was
changed to hide them. Maintainer follow-up: investigate that shared rule on
arithmetic-free controls; shared files are outside this chat's ownership.

The law packet's 56% essence and 42% inhabited-domain broken scores likewise
supply no concrete counterexample. Source review confirms explicit arbitrary
String domains, concrete nonempty/distinct/invalid witnesses, exact reverse
observations, and post-success/failure forward observations. Existing eight
semantic mutants check before their unchanged assertions fail. General
arbitrary-history refinement is explicitly not claimed. No unresolved *reported*
finding remains; these scores cannot establish completeness or a missing theorem.

## Verification and limits

Verified current sources against the published closure and the source hashes in
[deterministic gates](receipts/gates.json). That matching evidence contains a
zero-hole proof check, native/JS conformance, release consumer runs and eight
type-correct semantic kills; the audit verified their recorded outcomes. No Bend
source changed, so deterministic suites were not rerun merely for model scores.
Accepted laws and existing release evidence remain intact.

Perch reads files without a Bend AST/call graph and returns probabilities without
concrete defect explanations for these custom checks. Empty GPU/F32/foreign-effect
domains legitimately satisfy some rules; 84 checks are not 84 independent semantic
properties. Universal all-history refinement, physical maximum allocation and GPU
execution remain unverified. No production accuracy estimate follows from zero
reported defects or three control outcomes. Root review-log edits were prohibited
by assignment; the shared-rule observation is recorded here for the coordinator.
