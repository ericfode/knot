# OutputBuilder status

Complete: published and remotely verified on 2026-09-26.

Content hash: `0xc409b77d3230ca33374caf6b0993f0cb`. Official hub: https://hub.bend-lang.com.
Text import: `import 0xc409b77d3230ca33374caf6b0993f0cb/main.bend as Text`.
Bytes import: `import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as Bytes`.
Interface is stable for this immutable content identity. Dependencies: Base only.
Pinned seed: Bend 2.0.29 / 574b6d39a235b539eb19a5c532993a0abb3d11ad.
This package pin does not select Knot language compatibility.

Delivered persistent ordered text chunks and a distinct checked byte builder.
Text preserves exact Char order/newlines. Bytes validates 0..255, tracks checked
U32 length/limit, composes under the left limit and returns explicit errors.
No implicit encoding or LEB128. Construction is constant structural work except
byte-fragment validation; finishing is linear in emitted units plus tree nodes.

Verified:
- 27 filled law declarations, zero holes. Universal text/byte-tree refinement;
  checked byte length/validation has concrete normalization/runtime/source evidence.
- Native CPU: 14 named checks, including 512 text triples and 65 capacities.
- JS: 13 scalar-text/byte checks. Native raw-U32 Char also passes; JS rejects
  invalid Unicode scalars. No GPU, Wasm, or WebGPU execution claimed.
- Nine semantic mutants type-checked and compiled before intended runtime kills.
- Scaling at 1,000/2,000/4,000/8,000 chunks: tiny, uneven, empty and byte cases;
  exact outputs plus linear source-level census. Timings include the whole process.
- Exact 12-file upload closure: both law/proof pairs, models, APIs, conformance,
  example and MIT-0 LICENSE. Expected and returned content hashes match.
- Fresh BEND_LIB consumer imports only the remote hash, checks, compiles and runs
  on native and JS. All 12 fetched file SHA-256 values match the reviewed closure.

No release blockers. Live Perch audit completed 2026-09-26: 18 provider responses,
91 rule answers, no reported production findings. The dedicated rule detected
one intentional broken control and missed a held-out broken case at 79% against
its 80% floor; it remains advisory. See PERCH_REPORT.md. Original release-time
credential-unavailable receipts are preserved as historical evidence.

Receipts: RELEASE.json, evidence/closure.json, evidence/gates.json,
evidence/publish.stdout, evidence/publish.stderr, evidence/remote.json.
Reproduce using the three commands in RELEASE.json. Raw Buffer constructors are
unchecked: checked API users must not forge metadata. Runtime resource limits
and repeated-finish costs are documented in SPEC.md and INTERFACE.md.


A later bounded parsed Perch pass reviewed all 20 implementation declarations
with helper context plus the current law packet: 21 completed provider responses,
109 answers, no findings. No source changes; proof check and all 12 published
closure identities reverified. See PERCH_PARSED_REPORT.md and evidence/perch-parsed/.
