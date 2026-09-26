# IntMap status

**Complete — published and verified remotely, 2026-09-26.**

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
