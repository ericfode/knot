# Self-hosting and generated GPU execution

Approved 2026-09-26. The active goal starts at executable enum checkpoint
`a884b14` and support handoff `996c394`.

| Milestone | Required evidence | State |
| --- | --- | --- |
| Structural programs | Fields, pattern bindings, owned storage, transfer/drop, sound first-order structural recursion; tree transformations in actual Wasm, ownership and exhaustion negatives | In progress: structural checking/evaluation and seed CPU owning-store qualification |
| Compiler-shaped programs | Generic datatypes, dependent computation, quantities, closures/captures, local modules; generic AST walker and fueled evaluator | Pending |
| Language/library closure | Conversion, laws/proofs/rewrites, closed templates, required pure Base execution; Knot checks the whole pinned unmodified Base with privileged capabilities inventoried | Pending |
| Compiler components | Actual compiler components and exact transitive dependencies execute as Wasm through a narrow byte host | Pending |
| Whole bootstrap | Seed builds C1; C1 emits Wasm A2; A2 emits A3 from the same frozen complete bundle without upstream fallback; deterministic artifact equality and independent conformance on both generations | Pending |
| Generated GPU program | Self-built compiler emits Wasm/WebGPU for a bounded irregular recursive evaluator; captured values, ordered joins, suspension and adaptive redistribution execute on a real GPU and agree with the independent evaluator | Pending |

GPU storage, continuation, join and reclamation qualification begins alongside
structural runtime work. It must not wait until after self-hosting. Correct GPU
execution is required; a speedup is a separate measured claim.

Maintain three explicit inventories: the language used to implement Knot, the
language accepted by Knot, and host capabilities required by each artifact.
The seed, pure Base execution slice, privileged declarations, and transitive
dependencies all belong to the bootstrap closure. Source checking, a toy
self-compilation or a handwritten shader is not completion.

Each increment preserves the enum corpus, independent Bend evaluator, published
package ownership and GPU prototype. Source semantics stay in Bend. Record
Invalid, Unsupported, Exhausted and host/internal failure separately. Use the
deterministic law-quality and targeted Perch gates; commit verified increments
with explicit paths and a post-commit status check.

## Current increment

The structural term [checkpoint](../research/compiler-fields/README.md) adds
constructor arguments, flat patterns, effective quantities and reconstruction
of matched parents. The ordered match frontier is distinct from lexical IDs.
The independent evaluator executes live fields and skips erased fields. Its
persistent values are a semantic model. A separate owning-store component now
qualifies transfer/rejection and generation lifetime on the seed's CPU backends.
The emitter retains the enum capability boundary after complete body checking.

The support chat committed the [runtime support plan](RUNTIME-SUPPORT-PLAN.md)
in `bc99d21`: seven bounded probes for live-field projection, owning storage,
reusable Data lifetime, fresh handles, captures/joins, frontier ownership and
reclamation. The [owning-store checkpoint](../research/owned-store/README.md) now
qualifies R2 transitions and part of R4 freshness on native/Bun: 14 filled laws,
3,532 independent traces per backend, generation-boundary and quantity checks,
and six semantic mutants. This is not a device store or a proof of general heap
refinement. The package implementation campaign remains paused; no general Data
allocator or lifetime strategy is selected. Follow-up
`f4413c1` aligns the contracts with parent reconstruction, match identity and
compact live-field slots.

Next: checked flat Wasm/GPU record layout, live-field projection, handle-word
encoding and actual execution of the storage transitions. Arena-ID allocation
and restore require a lifetime contract; suspended roots, shared Data and partial
joins still need separate reclamation probes. Integrate storage into field
lowering and add sound structural descent. Recursion and real Wasm tree execution
remain required before milestone 1 is complete.

The compiler implementation now shares binding refinement/replacement through
a closed template ([bounded style checkpoint](../research/compiler-style/STYLE_CAMPAIGN.md)).
Its unchanged regression corpus passes; the accepted source language remains
the documented profile and the emitter remains enum-only. The new store uses
generic Type payloads, affine Arrays, reusable Data locators/lists and disposer
functions. Its trust inventory loads pinned Base and records IO.print as the
conformance host capability. Neither change closes the implementation-language,
whole-Base, Wasm bootstrap or generated-GPU requirements.
