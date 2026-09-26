# Self-hosting and generated GPU execution

Approved 2026-09-26. The active goal starts at executable enum checkpoint
`a884b14` and support handoff `996c394`.

| Milestone | Required evidence | State |
| --- | --- | --- |
| Structural programs | Fields, pattern bindings, owned storage, transfer/drop, sound first-order structural recursion; tree transformations in actual Wasm, ownership and exhaustion negatives | In progress: field declarations and catalog |
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

The structural declaration [checkpoint](../research/compiler-structural/README.md)
passes 16 pinned-seed fixtures, native/Bun metadata and rejection observations,
256/257-field bounds, five new filled laws and seven semantic mutants. The
original source-to-Wasm gate still passes and its generated modules are unchanged.
Field values and patterns remain outside the executable profile until their
checker and owned storage exist.

The support chat committed the [runtime support plan](RUNTIME-SUPPORT-PLAN.md)
in `bc99d21`: seven bounded probes for live-field projection, owning storage,
reusable Data lifetime, fresh handles, captures/joins, frontier ownership and
reclamation. They are proposed and unrun. The package implementation campaign
remains paused; no allocator or lifetime strategy is selected.

Next: field-pattern scope and refinement, logical live-slot projection, and the
independent ownership/handle model. Matching fields requires an explicit binder
order independent of lexical identity: fields replace their parent's match
position while later parameters remain matchable. Do not use increasing lexical
levels as that order once fields are inserted. Owned storage and real Wasm tree
execution remain required before milestone 1 is complete.
