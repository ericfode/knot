# Research Perch report — 2026-09-26

Scope: Compiler Planning owns `research/execution-models/` and
`research/adaptive-tasks/`. This report follows the project-wide live-review
request; it does not change any published package or shared rule.

**Completed: 14 targeted requests, 14 provider responses, 88 relevant checks.**
Twelve Bend files received all six Bend rules; two self-contained law packets
received all eight law rules. Perch 0.3.5 requested `jev-latest`; every response
reported **`jev-1.13.0`**. No findings met the configured reporting floors.
This is advisory semantic review, not a deterministic acceptance proof.

## Exact inputs and receipts

The [durable audit index](perch-audit.json) retains every wrapper receipt, full
rule/source/receipt hash, raw probability, provider count, and model ID. Original
receipts stay in ignored `.perch/usage/`; the retained copies keep this report
reproducible without private credentials. All source hashes matched at review.

| Input | SHA-256 | Checks | Original receipt |
|---|---|---:|---|
| [adaptive-tasks/LAWS.bend](adaptive-tasks/LAWS.bend) | `0c27192115eeb532b975fa642cd9d25e6e2187ca97431a838acfa20ec61bfc87` | 6 | [fd3312e8-8f45-4fc3-a6b4-e532e512b6ca](../.perch/usage/2026-09-26T20-44-35.929Z-fd3312e8-8f45-4fc3-a6b4-e532e512b6ca.json) |
| [adaptive-tasks/LAW_REVIEW.md](adaptive-tasks/LAW_REVIEW.md) | `696f199afe006ce33635be8ab392d455571b1ebb55624f44126ad73240c1b634` | 8 | [c5566bf3-4191-4ac2-a389-f8b7cf93b79c](../.perch/usage/2026-09-26T20-44-24.939Z-c5566bf3-4191-4ac2-a389-f8b7cf93b79c.json) |
| [adaptive-tasks/PROOF.bend](adaptive-tasks/PROOF.bend) | `f653d5802249799902e7fbaa33fff2868e7537fe3c272a92473f9f145ddd7125` | 6 | [83a41597-67b4-49e0-9bfe-64754bef85ae](../.perch/usage/2026-09-26T20-44-35.957Z-83a41597-67b4-49e0-9bfe-64754bef85ae.json) |
| [adaptive-tasks/conformance.bend](adaptive-tasks/conformance.bend) | `7f4e05b5f5c3317099bdaf9a4b45e20761c8b93e7d8f73667aa20fe978846713` | 6 | [b99829c6-cd58-49dc-a0c8-0d25d6ecf123](../.perch/usage/2026-09-26T20-44-35.982Z-b99829c6-cd58-49dc-a0c8-0d25d6ecf123.json) |
| [adaptive-tasks/fixtures.bend](adaptive-tasks/fixtures.bend) | `2f9b69eb971020e36ca2800d6327345819884b0c04497ce95f69cf9ebda01dac` | 6 | [bb54ea44-7db3-45b7-8527-cbfbfba12088](../.perch/usage/2026-09-26T20-44-35.902Z-bb54ea44-7db3-45b7-8527-cbfbfba12088.json) |
| [adaptive-tasks/oracle.bend](adaptive-tasks/oracle.bend) | `bd065f518ef381c777dae17e1cc2f9250b87e9db66d8b74f1b98ecd011926096` | 6 | [854a68e5-90c2-403a-8c80-149f07ba2c07](../.perch/usage/2026-09-26T20-44-24.989Z-854a68e5-90c2-403a-8c80-149f07ba2c07.json) |
| [adaptive-tasks/slot.bend](adaptive-tasks/slot.bend) | `f8350b71240146dc6061543d32b36ca40f0f420953e074b12f76b90389314cf2` | 6 | [e9295725-26c4-460c-bca3-e22371b716f6](../.perch/usage/2026-09-26T20-44-24.923Z-e9295725-26c4-460c-bca3-e22371b716f6.json) |
| [adaptive-tasks/task.bend](adaptive-tasks/task.bend) | `f0e822cdf6fd5d59d6b3069c750ef74995b58dcd3004e188b9980e1e07f82ca5` | 6 | [f9d76375-869d-48ca-9b16-c82659e55dcb](../.perch/usage/2026-09-26T20-51-06.242Z-f9d76375-869d-48ca-9b16-c82659e55dcb.json) |
| [adaptive-tasks/tests/affine-valid.bend](adaptive-tasks/tests/affine-valid.bend) | `04a1bf62271666e51ad9655d6ddf4aa075ec2b2e8bd1ecca1f7de223aa049a2d` | 6 | [51ab8f19-86ae-4fd3-b847-4f8819fe5c1c](../.perch/usage/2026-09-26T20-44-36.006Z-51ab8f19-86ae-4fd3-b847-4f8819fe5c1c.json) |
| [execution-models/LAWS.bend](execution-models/LAWS.bend) | `b41d7b34833835119e42df5f05c6866b7e60229075430b6205c0b78514df5dc7` | 6 | [6f593d15-a719-4c4d-a459-2c8f8ed31980](../.perch/usage/2026-09-26T20-44-36.043Z-6f593d15-a719-4c4d-a459-2c8f8ed31980.json) |
| [execution-models/LAW_REVIEW.md](execution-models/LAW_REVIEW.md) | `360bfa90f48be065de8e8a6991910c04be7f18a6b1fb0642780b9a73099ed35e` | 8 | [a533614f-9e6c-4e81-a0b9-6abea5de5b36](../.perch/usage/2026-09-26T20-44-24.971Z-a533614f-9e6c-4e81-a0b9-6abea5de5b36.json) |
| [execution-models/PROOF.bend](execution-models/PROOF.bend) | `f8f810df0a03411a89c59763c2bbc8e92c272a5b3f05264bac86a4b1999175f8` | 6 | [d27a1981-2aad-48fe-bd5a-d64d9bcf7f70](../.perch/usage/2026-09-26T20-44-36.055Z-d27a1981-2aad-48fe-bd5a-d64d9bcf7f70.json) |
| [execution-models/conformance.bend](execution-models/conformance.bend) | `58c4eeba48c9b2528de7f7517e07f086a0c597b550aa6797db462632db1179aa` | 6 | [200f1c13-1a26-443b-83ed-b7c082d210e6](../.perch/usage/2026-09-26T20-44-36.089Z-200f1c13-1a26-443b-83ed-b7c082d210e6.json) |
| [execution-models/model.bend](execution-models/model.bend) | `b17a6652281982118d0c19a063f9674ca918dfa693a85460e5adc5df1c6c99b9` | 6 | [aa559894-8e3f-499d-bc29-6387d8d4eb0f](../.perch/usage/2026-09-26T20-51-06.072Z-aa559894-8e3f-499d-bc29-6387d8d4eb0f.json) |

## Findings and adjudication

No emitted finding required a source fix. Confirmed defects, false positives,
duplicates, and unresolved emitted findings are each zero for this audit.
Below-floor probabilities are retained rather than treated as certainty. The
`probability_true` field concerns the rule holding; its complement is the
probability of a violation used by Perch reporting.

The lowest Bend rule scores concerned machine arithmetic. Manual inspection
found no size/index arithmetic in the join/slot models; adaptive payload
arithmetic is explicitly modular U32, while task fuel uses Nat. The wrong-tick
mutant changes the independently specified arithmetic observation and is
rejected. No rule threshold or correct implementation was changed to obtain
a clean report. The general law packets explicitly distinguish full-state
equations from lossy observations and arbitrary-budget induction from finite
CPU/device checks.

Known design limits remain open work, not hidden completed claims: the old
join is copyable Data; the new slot is affine but not an indexed arena; the
device storage is never reused within a run; full CPU/device simulation,
sharing, cancellation, generic closures, Wasm hosting, and source lowering are
unproved/unimplemented as specified in the packets.

## Deterministic evidence and review changes

- [Abstract join receipt](execution-models/evidence.json): 18 quantified
  transition equations, ten JS/native observations, four type-valid semantic
  mutants rejected. Existing source hashes remain current; unchanged gates
  were not repeated merely to refresh this report.
- [Adaptive receipt](adaptive-tasks/receipts/checks.json): 12 checked laws,
  including arbitrary-budget composition, eleven JS/native protocol
  observations, ten independently evaluated tree fixtures, two intended
  quantity failures with a valid neighboring control, and five Bend mutants.
- [Device receipt](adaptive-tasks/receipts/gpu.json): 38 Metal runs and 1,713
  dispatches on a non-fallback Apple M5 Max; three valid shader mutations fail
  result agreement. Explicit capacity/round failures are expected cases.
- During deterministic review, the one-tick law was written with an independent
  arithmetic RHS, rather than calling the implementation tick on both sides.
  The host checks every frontier word outside declared capacity, including
  capacity 0 and 1. The final harness run passes and hashes both changes.
- Added bounded research law packets. The Perch coordinator extended shared
  selectors; this chat did not alter shared rules or calibration thresholds.

Exact deterministic receipt hashes are retained in `perch-audit.json`.
No performance ranking or universal memory-safety proof follows from these runs.

## Exclusions and reproducible commands

The intentionally invalid `affine-task-reuse.bend` and `affine-slot-reuse.bend`
are excluded from clean-source Perch review; the deterministic harness requires
each to fail specifically in quantity checking. Vendor/toolchain sources,
node_modules, generated outputs, and temporary mutants were not scanned.
WGSL, JavaScript, and Python have **no Perch coverage in this report**. WGSL
has shader-validation/device/oracle checks; host code has input, bound,
canary, lifetime, and result assertions. Those do not replace a general review.

```sh
npm run lint -- research/adaptive-tasks/task.bend --rules bend-fuel-completeness,bend-machine-arithmetic,bend-borrow-lifetime,bend-ordered-f32,bend-effect-boundary,bend-device-stack --json
npm run lint -- research/adaptive-tasks/LAW_REVIEW.md --rules law-domain-inhabited,law-observable-essence,law-public-contract-coverage,law-independent-model,law-state-composition,law-boundaries-and-exhaustion,law-mutation-sensitivity,law-proof-claim-integrity --json
python3 research/adaptive-tasks/check.py
```

Repeat each targeted command with the corresponding input above only after a
material change or a new review concern. The audit index records the exact
rule set and source hashes for every completed check.
