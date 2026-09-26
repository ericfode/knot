# Source live Perch audit — 2026-09-26

**Outcome:** no reported findings on the package sources or final law packet. Both deliberately broken checkpoint controls were reported; both clean controls were not. No Bend semantics or accepted laws changed. All 13 files in the published upload closure still match release `0x88d5b48c03f82f217d3a2aa0656744f4` byte for byte. No republication.

## Execution and coverage

Used `npm run lint -- <path> --rules <names> --json` through the root receipt wrapper. Perch **0.3.5**, requested **jev-latest**, actual **jev-1.13.0**. **19 live requests, 19 provider responses, 100 rule evaluations across 18 distinct targets.** One law-packet recheck followed a documentation correction. No errors, rate-limit retries, zero-check results or offline substitutes counted.

The six file-level Bend rules were `bend-fuel-completeness`, `bend-machine-arithmetic`, `bend-borrow-lifetime`, `bend-ordered-f32`, `bend-effect-boundary`, and `bend-device-stack`. Each file below received all six and reported zero findings. Full raw probabilities, source hashes, rule-set hashes and original `.perch/usage/` receipt paths are retained in [the audit index](receipts/perch-audit-2026-09-26/index.json) and linked receipt copies.

| Bend file | Source SHA-256 | Receipt |
| --- | --- | --- |
| `LAWS.bend` | `bbd74050a1a1fc5ae7af9f8fce892023de197f8e37dcfdf87ef000af718f0950` | [7c85cf63](receipts/perch-audit-2026-09-26/7c85cf63-f472-4408-9b59-2c14d09a2a0c.json) |
| `PROOF.bend` | `06e8c1044639d44fbfc6eeea3618b8dc8a4f75c25a2409918c97c86deda782af` | [fc5f45e9](receipts/perch-audit-2026-09-26/fc5f45e9-ec3c-4332-a0cd-5a69cb1a59ee.json) |
| `benchmark.bend` | `d28dbdb645e5e132917653cf8434f59a37c4b0438944af28a430fbb1771793b8` | [d7dc33ba](receipts/perch-audit-2026-09-26/d7dc33ba-75bc-469a-bc72-5e9cc14427b7.json) |
| `conformance.bend` | `93ede95e703f52c7efe436a98681d6003068b10819e423a1c3a3c0012f9e0c69` | [ea9e1bf7](receipts/perch-audit-2026-09-26/ea9e1bf7-16d6-440b-8619-a360ae0966fb.json) |
| `example.bend` | `d1e38d7f3f98a1db77eca3df5640fd1b67ad5b0a815162b2e1d6d12313a70800` | [94dd51ba](receipts/perch-audit-2026-09-26/94dd51ba-863f-4751-a6f1-f3ca576d2784.json) |
| `main.bend` | `83029b603921ea8a978c3f9a424fb256e0737d8041836c2749f8bd1b5e0be12c` | [3ccf0268](receipts/perch-audit-2026-09-26/3ccf0268-2540-4043-bd20-e8d2ee165462.json) |
| `model.bend` | `2ba69937a36ee689bec25bcc2f99a83bdcf8373eb88e30813800388d7a8495ea` | [e8233c6e](receipts/perch-audit-2026-09-26/e8233c6e-3e69-4213-8f0a-f9cb29a03749.json) |
| `observations.bend` | `c0d4d88f9e6324db3ec5698280d5ffa807b5b78304d02127fb6b75627ce39cb0` | [d5954c30](receipts/perch-audit-2026-09-26/d5954c30-2f7b-4588-b4e8-f905d32f4106.json) |
| `proof_observations.bend` | `495a5d4767a750b176387d568489a556e23af935e8a05960c12839ce2ce4fc1f` | [9d1c2537](receipts/perch-audit-2026-09-26/9d1c2537-6d1b-4c61-ad95-c2f8c631fbac.json) |
| `release.bend` | `e5cd3a2902d6f871978777683442df9fe03f76221f37058a1b56212b7e469adb` | [5e9ba568](receipts/perch-audit-2026-09-26/5e9ba568-cea8-4e88-87c7-b53fd53ef431.json) |
| `types.bend` | `43e2cd88043f6f1b7c183e017931bc68dabae516b35a4eab9e319187442a9141` | [9ce1740a](receipts/perch-audit-2026-09-26/9ce1740a-cfd0-4e19-82cb-a1d166e45cec.json) |
| `tests/invalid_scalars.bend` | `47ff1cdf3a9d1609b240994dc1773a197644a8d6c7368dfc7aa6798e8a8c49f0` | [cb77e64a](receipts/perch-audit-2026-09-26/cb77e64a-014c-402c-8440-094e1768e4c4.json) |
| `tests/remote_consumer.bend` | `80ca825096ceda7e3cc1fcb6bb5fa2106a42ea535e9062695c54445b2849fc7d` | [b4fed399](receipts/perch-audit-2026-09-26/b4fed399-aadc-4496-b983-1bf7dbeb0411.json) |

No maintained Bend source was excluded, including the small type/release/example files, the malformed-scalar test and the remote consumer. Excluded `build/**` consists of generated output, copied mutation variants, benchmark drivers and downloaded cache copies. Those are derivatives, not additional maintained implementations. Host orchestration scripts were outside this Bend-rule audit; malformed-scalar rejection tests were included, not silently excluded as negatives.

## Law packet

The real `LAW_REVIEW.md` received all eight `law-*` rules plus `source-checkpoint-observation`, nine checks per request. Initial receipt [c10d905c](receipts/perch-audit-2026-09-26/c10d905c-7760-45bb-9088-2d385ca740c8.json) had no findings. The final packet, after correcting its stale credential note, also had no findings:

- SHA-256: `6fcc66fcd55d34ee38b2624f7b8ad41969ceb8f64ceaa7dbb2a1af3a6636fd16`.
- Receipt: [f154332e-bc12-4c37-b5f3-ee048a644b34](receipts/perch-audit-2026-09-26/f154332e-bc12-4c37-b5f3-ee048a644b34.json).
- Final broken probabilities: inhabited domain 38%, observable essence 63%, public coverage 41%, independent model 39%, state composition 26%, boundaries 41%, mutation sensitivity 30%, proof integrity 47%, checkpoint 14%. Shared law floor: 80%; checkpoint floor: 70%.

## Dedicated-rule controls and adjudication

Rule unchanged at **floor 70%, advisory**; SHA-256 `a600fbba95db9304f17dc2ec82743eea2eac2f681b09357718044c7f6958dbc5`. The prior calibration in `docs/perch-calibration/source-checkpoint-2026-09-26.json` recorded clean/broken/held-out-clean at 20%/76%/19% broken probability and the move from 80% to 70%. This audit preserved that floor and added a fresh held-out broken case after the floor was fixed.

| Control | Expected | P(true) | P(broken) | Reported at 70% | Adjudication / receipt |
| --- | --- | --- | --- | --- | --- |
| `clean.md` | clean | 77% | 23% | no | Correct clean control; [48c615e8](receipts/perch-audit-2026-09-26/48c615e8-4683-445b-9c25-2c16ebe48323.json) |
| `broken.md` | broken | 25% | 75% | yes | Confirmed intentional defect; [0a96f69b](receipts/perch-audit-2026-09-26/0a96f69b-6ffd-4dba-9eb4-972d84908a37.json) |
| `held_out.md` | clean | 82% | 18% | no | Correct clean control; [e0d71537](receipts/perch-audit-2026-09-26/e0d71537-5123-44b3-851d-df9979e93336.json) |
| `held_out_broken.md` | broken | 25% | 75% | yes | Confirmed intentional defect; [e7f2c857](receipts/perch-audit-2026-09-26/e7f2c857-b628-4d97-9e14-6f30f303fc8c.json) |

Both emitted findings are **confirmed control defects**, not defects in Source. Their expected restored cursor is derived from the checkpoint under test, so a checkpoint that silently changes the original offset can satisfy the assertions. The original cursor is never independently compared. The real `observations.bend` checks `cursors_eq(Source.checkpoint(c),c)` and the existing `rewind_checkpoint` mutant is killed by the unchanged witness; see `receipts/mutations.json`. The fresh held-out broken case uses original offset 3, two bumps, and expected fields read from `saved`, independently of the earlier offset-1 fixture.

**Misses:** none among these four controls at the current floor. Both broken cases scored 75%, so both would be missed at the former 80% floor. This is four bounded control observations, not a production accuracy estimate. No rule wording or threshold was changed during this audit.

## Below-floor signals and deterministic review

There were no emitted production findings to classify as confirmed, false-positive, duplicate or unresolved. Below-floor arithmetic probabilities were 57–74% across the Bend files. These scores are retained rather than described as strong clean verdicts. The highest, 74%, was on `release.bend`, which only imports modules and delegates to `Example.main()`; it contains no arithmetic. `types.bend` likewise contains only data declarations. Those scores provide no concrete visible arithmetic defect, and the rule forbids inferring unseen problems. No semantics were changed to reduce them.

For `main.bend` (58% arithmetic), source inspection confirms construction caps length at 16,777,215; bump adds one only after a non-EOF read; binary search maintains ordered bounds; reverse-location width is checked before addition. Fuel exhaustion returns `BadIndex`/`IndexInvariant`; 25 steps cover at most 2^24 line starts. For model/test helpers (including 61% on `model.bend`), their actual use is the bounded Source domain and documented finite fixtures; no arbitrary-size model or GPU promise is made. These reviews did not identify an in-contract defect. They are not proofs of all-state refinement.

Fresh deterministic verification passed: zero-hole `PROOF.bend`, native and JS conformance (result `1`), and native malformed-character rejection (`1`). [Commands and results](receipts/perch-audit-2026-09-26/deterministic.json). All published source hashes and the inputs to the prior eleven semantic mutation tests are unchanged; mutation and scaling workloads were not rerun unnecessarily.

## Changes and remaining limits

Added this report, retained live receipts, a targeted audit driver and one held-out broken control. Corrected the release-time “credentials absent” wording in `LAW_REVIEW.md` and `STATUS.md`; the changed packet received its final live recheck. Historical release receipts and `RELEASE.json` remain unchanged; their document snapshots describe release time. No `.bend` file, accepted law, implementation, or package rule changed.

Perch has no Bend AST/call graph. Its answers are advisory probabilities without a concrete explanation here; the zero findings and control separation do not establish completeness, universal refinement, backend correctness or GPU support. Existing no-GPU/all-string-refinement limitations remain. Credentials and environment values were neither printed nor copied. Shared rules and logs were not edited; the coordinator can use this report for the maintenance record.
