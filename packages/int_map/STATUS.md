# IntMap status

**Published release verified remotely, 2026-09-26. Working source has an
unreleased style revision.**

**Additive edit-locality proof accepted, unreleased (2026-09-27).**
`locality/LAWS.bend` and `locality/PROOF.bend` derive insertion/deletion lookup
guarantees from one shared pair of child-projection laws. Eight new filled laws
and the original 23 check with zero holes after one retained parser-diagnostic
retry. Native/JS conformance, all 11 original mutants and scaling/model gates
pass; all 70 frozen inputs, including runtime and old proofs, remain identical.
Thirty-one supplementary semantic checks report no findings. Canonical Perch
proof parsing lacks imported template-law context; an exact mechanical review
copy supplies supplementary ratings. Three of eight law/fill pairs meet all
five targets, and the expanded composition remains below expressive targets.
This is a retained proof abstraction, not a full style pass. See
[the report](campaigns/edit-locality-1/README.md). No new runtime timing or release.

Latest bounded trial **int-map-paths-2 is accepted, unreleased (2026-09-27)**.
It shares insertion/deletion rebuilding through edit_path while retaining their
Entry/Tip endpoints and raw/pruning branch rules. The exact first candidate
passed unchanged proofs, native/JS conformance, all 11 mutants and scaling/model
checks; 39 targeted semantic checks reported no findings.

A focused timing follow-up measured 3.1% native and 5.4% JS slower medians at
4096 entries. The user explicitly authorized up to 20% degradation, so this
regression is accepted as deferred performance work. Seven supporting style
declarations pass; the leading recurrence and whole-file composition remain
below Memetic/Anticipation/Payoff targets. No full style pass or nonregression
claim. See [STYLE_CAMPAIGN.md](STYLE_CAMPAIGN.md) and campaigns/int-map-paths-2
for the candidate, raw evidence and changed performance allowance. The published
hash and dependency pins remain unchanged.

Batch int-map-paths-1 simplifies only `branch` to an empty-pair case and a
binding fallback. Fixed proofs, native/JS conformance, all11 mutants and scaling
gates pass;29 targeted semantic checks reported no findings. All four reviewed
declarations meet compression and delight targets, but remain below memetic
target. No all-axis style pass. See [STYLE_CAMPAIGN.md](STYLE_CAMPAIGN.md) for
source identities, before/after evidence and remaining work. The published hash
and its historical receipts below remain unchanged; current main.bend differs.

## Historical release and subsequent audits

Content hash: `0x99e32f5f97dad3791a32b01d133555c5`.

```bend
import 0x99e32f5f97dad3791a32b01d133555c5/main.bend as M
```

Interface stable: eight public operations in INTERFACE.md. Pure persistent
U32 trie, all 32 bits, copyable Data values. Base only; no sibling dependency.
MIT-0 original code. Pinned Bend 2.0.29 at
574b6d39a235b539eb19a5c532993a0abb3d11ad; no broader compatibility selection.

Verified gates:
- 23 filled law declarations, zero holes: 7 public universal theorems (two with
  constructive separated-path premises), 9 auxiliary/structural theorems,
  1 explicit high-bit witness, and 6 concrete normalization laws.
- Native CPU and generated JavaScript: nine conformance families plus example.
  Includes all 32 single-bit/complement positions, max U32, stored zero versus
  absence, overwrite/removal, exact fold contents/order/seed, prior versions,
  192 model-based composed transitions and 96-entry independent-model unions.
- 11/11 semantic mutants killed by intended unchanged observations. Each first
  passed the pinned checker and executable build; no syntax/type failures counted.
- Scaling at 64,256,1024,4096 entries: dense and 16-shared-low-bit layouts;
  depth 32; exact lookups, sum, size; full erasure leaves zero retained nodes.
  Independent association-list validation runs outside benchmark timing.
- Exact upload closure reviewed: eight Bend sources plus LICENSE; laws, filled
  proofs, independent model and conformance are included. No unrelated files.
  Expected and returned content hashes match.
- Fresh initially empty BEND_LIB downloaded all 9 files. Every SHA-256 matched
  the reviewed closure. Remote native and JS consumers compiled and executed
  the full release tests and a separate persistent noncommutative-union check.

Evidence: RELEASE.json, receipts/gates.json, receipts/closure.json,
receipts/mutations.json, receipts/performance.json, receipts/perch.json.
`python3 packages/int_map/scripts/check.py` reproduces deterministic local gates.
`python3 packages/int_map/scripts/publish.py` verifies frozen gates, publishes,
and verifies a new remote cache; publication already completed.

Live Perch audit completed 2026-09-26: 18 provider responses from jev-1.13.0,
94 rule evaluations covering all 11 maintained Bend files, the real law packet,
and four dedicated controls. No source/packet finding reached the floor; both
broken controls were detected. The rule remains advisory. See PERCH_REPORT.md.

Manual audit found and fixed local benchmark CLI bounds in scaling.bend, which
was never uploaded: native/JS checks now reject zero and values above 4096 before
starting work. Six changed-file Perch checks and 36 runtime regression cases
passed. All nine published files remain byte-identical; no republish occurred.
Release-time missing-credential receipts remain preserved historical evidence.

Limits: no GPU execution claim, no full universal list-model refinement or
U32 bit-injectivity theorem, no heap-allocation telemetry. Fold/size/union
behavior is covered by concrete laws and runtime/model checks, not a universal
refinement proof. SPEC.md describes the reachable-map domain, native/unsafe
trust dependencies, temporary path allocations, and reclamation costs.

Fresh bounded declaration review (2026-09-26): 223 checks, 24 completed provider
responses, 23 source declarations plus the law packet, no reported package
findings. Proof and native/JS conformance rerun successfully. No package code or
published source changed in this pass. PERCH_DECLARATION_REPORT.md records exact
scope, context limits, receipts and a shared wrapper-metadata proposal.
