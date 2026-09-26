# OutputBuilder live Perch report — 2026-09-26

**Complete: 18 live provider responses, 91 rule answers, zero reported findings
in production sources or the real law-review packet.** One intentional broken
control was detected; the held-out broken control was missed at the reporting
floor. No package defect was confirmed and no Bend source or rule was changed.
The published release remains `0xc409b77d3230ca33374caf6b0993f0cb`.

Perch **0.3.5**, requested model `jev-latest`, actual model **jev-1.13.0** on all
18 receipts. Every request used `npm run lint -- <file> --rules <names> --json`.
Each source request checked six rules, the real packet checked nine, each
control checked one. Every checked rule has a raw provider probability. There
were no zero-coverage, provider-error, rate-limit or retry results.

Full source hashes, exact selected rules, timestamps, receipt IDs and original
`.perch/usage/` receipt paths are in [the audit index](evidence/perch-live/index.json).
Package-local receipt copies retain raw probabilities and actual model IDs.
[Summary](evidence/perch-live/summary.json) records coverage and adjudications.
Rule texts are frozen in `evidence/perch-live/{bend-rules,law-rules,package-rule}.yaml`.
No credentials were read, copied or included in these artifacts.

## Exact coverage

All 13 listed Bend files received all six file rules: `bend-fuel-completeness`,
`bend-machine-arithmetic`, `bend-borrow-lifetime`, `bend-ordered-f32`,
`bend-effect-boundary`, `bend-device-stack` (**78 answers**).
These are source-text checks; Perch has no Bend AST or inter-file call graph.

| Source | SHA-256 | Receipt / result |
| --- | --- | --- |
| `main.bend` | `4121b71f530bbb0d4cb05f7ff2ce3f2f65bbe5a5e3c1bb2f059a15b2c0491bb8` | [6 checked, no findings](evidence/perch-live/main.receipt.json) |
| `BYTE_LAWS.bend` | `cffc93ff7f84fec0e39e26fabdd8ee1b74a93f34cbf875403acc7d44d76b599a` | [6 checked, no findings](evidence/perch-live/BYTE_LAWS.receipt.json) |
| `BYTE_PROOF.bend` | `969180966cbeebb904be36ba3a84b69147a47c64f22eaaad14e82b4160a54df9` | [6 checked, no findings](evidence/perch-live/BYTE_PROOF.receipt.json) |
| `LAWS.bend` | `7c0b887642a77a3b8522b9c05a66ae61045b618b6bd062510530f5a2a783b569` | [6 checked, no findings](evidence/perch-live/LAWS.receipt.json) |
| `PROOF.bend` | `b6851d6a3738b754309c7d803f39c6c5e7e3d5eec6c376f83b8f61cc53d539f7` | [6 checked, no findings](evidence/perch-live/PROOF.receipt.json) |
| `byte_model.bend` | `d70023c2847de95e68f84db86f42c5fc7f1ed094166a492f2d108319ef43a396` | [6 checked, no findings](evidence/perch-live/byte_model.receipt.json) |
| `bytes.bend` | `b1c672949a72bcbc37509e31a1a20715eb73813904a50157328ded9ed0069ff1` | [6 checked, no findings](evidence/perch-live/bytes.receipt.json) |
| `conformance.bend` | `f1f4bc8a01dbfa28fc62298ac3185fdcdca7e23569ed929ed8bf692ccd54ced5` | [6 checked, no findings](evidence/perch-live/conformance.receipt.json) |
| `example.bend` | `8ab3b54a35ecd7e3ee1112fe0a80cb4d3c1c59930e906c116c564f7418c08ad3` | [6 checked, no findings](evidence/perch-live/example.receipt.json) |
| `model.bend` | `5a38de9bb16563d90077fd3e112084a420cc3b2cd55492a0e03c11d7c9101157` | [6 checked, no findings](evidence/perch-live/model.receipt.json) |
| `performance.bend` | `aca3145dfcc2ed0582c9781c4ecd404dd9c54e662c2e6f7eb6dce89eff6e9560` | [6 checked, no findings](evidence/perch-live/performance.receipt.json) |
| `release.bend` | `d13eb60779d4941ebbfdec4478345c61ec60dc0f8118f2ef3e7a1910966fd988` | [6 checked, no findings](evidence/perch-live/release.receipt.json) |
| `evidence/remote-consumer.bend` | `4bfb40590d5acb8fe6ed25013f5f3f410ce60920992e3694de7cfdcac93a0cd3` | [6 checked, no findings](evidence/perch-live/remote-consumer.receipt.json) |

`LAW_REVIEW.md` received all eight `law-*` rules plus
`output-builder-linear-assembly`: **9 checked, no findings**.
Input SHA-256: `6d2902b82d19ef9eedc02c25257bf6e64903a5bfa370023d827e9498c01bca57`.
[Packet receipt](evidence/perch-live/law-review.receipt.json).
The packet's credential-unavailable language is historical release evidence;
this live report supersedes that status without rewriting the audited input.

No substantive maintained Bend source was excluded. Even trivial `release.bend`,
the example, performance fixture, and generated remote consumer were included.
Excluded `build/`: generated compiler outputs, benchmark/portable wrappers,
remote-cache duplicates of published sources, and intentional negative mutant
copies. The latter belong to deterministic mutation testing and are not clean
production targets. Host Python/TypeScript drivers are outside the requested
six Bend file-rule scope. Markdown controls receive the dedicated rule below.

## Findings and controls

Probabilities below are **P(rule broken)**, derived as 1 minus the provider's
raw P(rule holds). The package reporting floor remains **80%**, advisory.

| Control | Expected | P(broken) | Reported | Adjudication |
| --- | --- | --- | --- | --- |
| [broken](evidence/perch-live/control-broken.receipt.json) | broken | 82% | yes | confirmed intentional defect |
| [clean](evidence/perch-live/control-clean.receipt.json) | clean | 54% | no | correct non-finding |
| [held_out](evidence/perch-live/control-held_out.receipt.json) | clean | 32% | no | correct non-finding |
| [held_out_broken](evidence/perch-live/control-held_out_broken.receipt.json) | broken | 79% | no | missed intentional defect |

**Confirmed control finding:** `broken/LAW_REVIEW.md` rebuilds the complete prior
output on every append via `fragment(String.append(finish(b),s))`. For n
one-character fragments this copies 0+1+...+(n-1) prior characters, contradicting
its linear total-work claim. This is intentional control corruption, not the
production tree implementation. The finding is correct.

**Known false negative:** `held_out_broken/LAW_REVIEW.md` claims O(N) finish cost
independent of chunk count while permitting arbitrary empty chunks. At N=0,
visiting K nodes still takes O(K), so that claim is false. Perch returned 79%
broken, below 80%, and therefore missed it. Clean/held-out clean returned 54%/32%.
The small control sample does not justify promotion or an accuracy estimate.
No threshold was raised or lowered to hide a result; the rule remains advisory.
No wording refinement was attempted, so there is no before/after calibration
claim. The separate Source checkpoint rule's calibrated **70%** floor and
`docs/perch-calibration/source-checkpoint-2026-09-26.json` were read and left intact.

**Production adjudication:** zero reported findings; therefore no confirmed,
false-positive, duplicate or unresolved production findings to classify.
Below-floor scores were inspected too: machine-arithmetic assigned 76% broken
to `release.bend`, whose sole operation calls `Example.main()` and performs no
visible arithmetic. It is weak signal, not a concrete wraparound counterexample.
The byte implementation compares count < room before incrementing and compares
right length <= cap-left length before adding, under its documented checked-API
invariant. Empty/refinement/snapshot laws and exact content tests already cover
the observations; no accepted law was weakened to accommodate a probability.
The package LAW_REVIEW result is 18% broken for linear assembly and at most 60%
for shared law rules. None is a correctness proof.

## Changes and deterministic verification

Added only this report, a reusable audit driver, retained audit receipts and a
status update. No Bend semantics, accepted laws, dedicated rule, shared file or
published source was edited. No republication was performed. All **12 release
closure SHA-256 values still match RELEASE.json**.

Fresh deterministic checks during this audit:

- Complete release/proof entry: `All terms check.` (all 27 law declarations filled).
- Newly built native conformance: **14 PASS** checks.
- Newly emitted JS scalar-text/byte conformance: **13 PASS** checks.
- [Verification receipt](evidence/perch-live/verification.json),
  [proof check](evidence/perch-live/proof-check.txt),
  [native output](evidence/perch-live/native-run.txt),
  [JS output](evidence/perch-live/js-run.txt).

The nine type-correct semantic mutant kills and scaling measurements remain
frozen release evidence in `evidence/gates.json`; they were not rerun or inflated
into new audit results. Their source hashes still match current code.

Remaining limits: no GPU/Wasm execution claim; JS text accepts Unicode scalars;
checked-byte validation/metadata preservation is supported by concrete/runtime
and source evidence rather than a universal history theorem. Perch's failed
held-out control confirms it cannot replace the deterministic gates. The
readable snapshots of rule text and per-file receipts make future comparisons
possible without claiming these four controls establish production accuracy.

For the coordinator's shared review log: retain the 79% held-out empty-chunk
miss and 54% clean-control score as package-rule calibration evidence. This chat
did not edit the shared log because the audit ownership boundary excludes it.
