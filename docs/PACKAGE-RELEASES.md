# Published compiler-support packages

Completed 2026-09-26. All six priority packages were published to BendHub and
verified through consumers using fresh caches on native CPU and JavaScript.
The coordinator checked package identities, source and dependency hashes,
gate inputs, mutation outcomes and release evidence. The follow-up heartbeat
is paused. [Machine-readable catalog](../packages/releases.json).

| Package | Published hash | Evidence and exact scope |
| --- | --- | --- |
| Vec | `0xd684886d10b431b9dce6c3b2d1ef1980` | [Release](../packages/vec/RELEASE.json), [contract](../packages/vec/SPEC.md), [laws](../packages/vec/LAW_REVIEW.md) |
| Source | `0x88d5b48c03f82f217d3a2aa0656744f4` | [Release](../packages/source/RELEASE.json), [contract](../packages/source/SPEC.md), [laws](../packages/source/LAW_REVIEW.md) |
| OutputBuilder | `0xc409b77d3230ca33374caf6b0993f0cb` | [Release](../packages/output_builder/RELEASE.json), [contract](../packages/output_builder/SPEC.md), [laws](../packages/output_builder/LAW_REVIEW.md) |
| IntMap | `0x99e32f5f97dad3791a32b01d133555c5` | [Release](../packages/int_map/RELEASE.json), [contract](../packages/int_map/SPEC.md), [laws](../packages/int_map/LAW_REVIEW.md) |
| Symbols | `0xf5507d46d06a1a8043dcb1a582194615` | [Release](../packages/symbols/RELEASE.json), [contract](../packages/symbols/SPEC.md), [laws](../packages/symbols/LAW_REVIEW.md) |
| TermStore | `0xce7bfa94c40ded8493cdb39d330add0c` | [Release](../packages/term_store/RELEASE.json), [contract](../packages/term_store/SPEC.md), [laws](../packages/term_store/LAW_REVIEW.md) |

```bend
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as Vec
import 0x88d5b48c03f82f217d3a2aa0656744f4/main.bend as Source
import 0x88d5b48c03f82f217d3a2aa0656744f4/types.bend as SourceTypes
import 0xc409b77d3230ca33374caf6b0993f0cb/main.bend as TextOutput
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as ByteOutput
import 0x99e32f5f97dad3791a32b01d133555c5/main.bend as IntMap
import 0xf5507d46d06a1a8043dcb1a582194615/main.bend as Symbols
import 0xce7bfa94c40ded8493cdb39d330add0c/main.bend as TermStore
```

Each hash also includes a `release.bend` entry containing its laws/proofs.
Source, Symbols and TermStore pin the Vec hash above. All use explicit MIT-0
licenses and were built with Bend 2.0.29, revision
`574b6d39a235b539eb19a5c532993a0abb3d11ad`.

## Validation and limits

All complete proof entries check with zero holes. Every package has an
independent model, concrete domain witnesses, a public-operation matrix,
composition and boundary checks, and semantic mutants that first type-check.
Across the six packages, 58 listed non-equivalent semantic mutants were killed
by the intended behavioral assertions. The reports distinguish universal
theorems, fixed-shape quantified laws, concrete normalization and runtime checks.
These are not general all-history refinement proofs for every optimized API.

Native CPU and JavaScript were exercised. Wasm/GPU execution is unvalidated.
Vec and TermStore accept Data payloads and thread affine ownership of the store;
they do not implement an affine runtime heap. Source uses Unicode scalar
offsets, caller-managed file IDs and LF-only line starts; it does not convert
UTF-16 offsets. IntMap's fold order is deterministic low-bit-first order rather
than numeric order. Symbols assigns IDs in first-intern order and retains Base
Map's prefix-sensitive lookup cost; it does not provide canonical cross-build
renumbering. OutputBuilder supplies distinct text and raw-byte paths, with
linear work in emitted length plus chunk count and no unbounded stack guarantee.

Package benchmark receipts record workloads and their measured limits. Native
lowering and scope-specific source cost arguments accompany timings. Compatibility
with another Bend version, a whole compiler, or a device backend is not inferred.

## Workflow improvements

Eight shared law rules and six narrow package rules are installed. Offline
selection/request checks passed. Live calibration was unavailable at release
time; the subsequent [Perch audit](perch-audit-2026-09-26.md) records completed
provider responses and 19/24 shared-law controls classified correctly, with five
missed violations. All model rules remain advisory. Later review does not
rewrite the original release receipts or establish stronger proof claims.

Two concrete audit findings strengthened [the deterministic law gate](LAW-QUALITY-GATE.md):

- A content projection that discards empty slots can hide a stale logical length.
  Public metadata, bounds and contents must agree; a separate Vec length law
  now rejects that semantic mutant.
- A negative fixture that fails in parsing cannot establish a type or ownership
  restriction. Vec's fixture was corrected and rechecked for the intended
  Data-versus-Type diagnostic; its published source hash remained unchanged.

The gate also records the intended violated observation separately from the
first rejecting law. Regression controls preserve these cases. A missing key,
zero rule coverage, syntax failure or unrelated test error never counts as a
successful semantic validation.

The [execution-model dependency handoff](EXECUTION-MODEL-DEPENDENCIES.md) records
follow-on work such as affine owning slots, bounded frontiers, join records and
checked binary encoding. Those are outside these six completed releases.
