# Self-hosting and generated GPU execution

Approved 2026-09-26. The active goal starts at executable enum checkpoint
`a884b14` and support handoff `996c394`.

| Milestone | Required evidence | State |
| --- | --- | --- |
| Structural programs | Fields, pattern bindings, owned storage, transfer/drop, sound first-order structural recursion; tree transformations in actual Wasm, ownership and exhaustion negatives | In progress: structural checking/evaluation, seed CPU owning store and Bend-emitted word-store transitions in real Wasm |
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

## Immediate priority: memetic foundation

Later on 2026-09-26, the user explicitly put the memetic issue before further
compiler implementation because it will shape the design. NLP here means
neuro-linguistic programming. The [research and recommended approach](../research/compiler-style/MEMETIC-THEORY.md)
and [first reading specimen](../research/compiler-style/MEMETIC-PRIMER.md) make
that work concrete. They propose exemplar development, imitation and transfer
before codifying a style, with owned unfinished computation as the leading
identity hypothesis.

The [hill-climbing plan](../research/compiler-style/MEMETIC-HILLCLIMB.md) now
specifies that comparison: competing directions, focused variants, reconstruction,
transfer and owner-led propagation. Its proposed first epoch has at most nine
substantive candidates across three rounds; it is not active and does not enlarge
the existing pilot's attempt budget. The next increment prepares the frozen
first-family packet, comparison cards and complete transfer contract, and
reconciles the existing pilot evidence with its owner. Establish concrete reading
preferences before model ratings; preserve independent semantic gates and the three style
targets. The existing scoped pilot remains unresolved and the wider campaign
queue stays held. A research note or evocative phrase does not resolve the
foundation. Do not automatically resume field-layout/emitter implementation
because this documentation has been committed. All six milestones above remain
required; this instruction changes their immediate sequencing, not the goal.

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

The [flat-store increment](../research/flat-store/README.md) now emits a 1,050-byte
Wasm module from Bend. Native/Bun emitter bytes agree; each lane runs 3,534 store
instances and compares 13,621 complete step observations against the independent
Bend list model. Fifteen codec/encoding laws are filled, 24 literal probes and
seven lifecycle checks pass per backend, and nine valid-module semantic mutants
are rejected. This qualifies word-store transitions and bounded address/word
encoding, not generic object reclamation or device execution. A discovered
aliased-buffer assertion is repaired and distinguished by a reinit-write mutant;
the original receipt remains qualified as historical evidence.

After the memetic foundation: compact mixed-width field layout, live-field
projection, an independently qualified twelve-byte locator transport and GPU
storage transitions. Arena-ID allocation and restore require a lifetime contract;
suspended roots, shared Data and partial
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
