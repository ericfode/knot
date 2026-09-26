# Runtime support for structural Bend and reproducible Wasm

2026-09-26. Coordinator handoff to Compiler Planning. The approved longer goal
is full Bend self-hosting through reproducible Wasm A2/A3, followed by
compiler-generated WebGPU adaptive continuation tasks. The
[active goal](SELF-HOSTING-GOAL.md) requires GPU storage, continuation, join and
reclamation qualification alongside structural runtime work, before bootstrap
completion. Final generated-device acceptance follows A2/A3. The
[bootstrap protocol](BEND-SUBSET-STAGES.md#bootstrap-protocol-and-first-self-compiling-stage)
defines A2/A3 and the independent conformance obligations. This plan supplies
early runtime contracts; it does not claim that the structural compiler or any
new runtime package is implemented. The six-package campaign remains paused.

Compiler Planning owns `src/`, structural fixtures and compiler/runtime
integration. Existing package owners retain their published sources. No new
package assignment, publication or memory-management strategy is selected here.

## Reference constraints and layout model

A bounded pinned-reference pass of the 13 current structural fixtures produced
the expected seven successes and six rejections. The
[receipt](runtime-support-reference-2026-09-26.json) preserves source text/hashes,
commands, diagnostics and Bend 2.0.29 reference identities. It confirms
declaration acceptance, not runtime field allocation or Knot structural support.

- A live field of a `Data` declaration must have `Data` kind.
- A `+` field requires `Data` even inside a `Type` declaration.
- An erased field may have `Type`; the runtime contract gives it no argument,
  storage slot, capture, tracing edge or drop action. Its declaration remains
  available for scope/type checking.
- Forward and mutual datatype references are accepted. Register all datatype
  identities/kinds before resolving fields. A datatype dependency cycle is not
  evidence of a cyclic runtime value, nor of an inhabited datatype.
- Field names are unique within one constructor; reuse across constructors is
  allowed. Validate unused declarations as well as reachable ones.

Keep declaration-order metadata for each constructor field: name, source span,
declared type identity, quantity, declaration index and optional live-slot index.
For declaration position `i`, its slot is absent when `q[i]=0`; otherwise its
slot is the number of earlier non-erased fields. Live slots form the contiguous
range `[0, live_count)`, preserving declaration order. A slot is a logical field
position, **not necessarily one machine word**. Width, alignment, offset and
representation class belong to a separate checked target layout.

Quantity and kind are separate. A quantity-1 binding remains affine even when
its value has `Data` kind. A reusable representation must not relax source
quantity checking. A live `Type` child transfers ownership; a reusable `Data`
value may be copied or shared under the selected representation's lifetime
contract. Duplicating raw handle bits does not duplicate an owning permission.

Resolve recursive references without recursively expanding an infinite inline
layout. Indirect recursive edges need fixed handle layouts; a proposed inline
representation needs cycle detection and an explicit rejection/indirection rule.
Two-pass declaration resolution is required now. SCC analysis is needed only
where a later layout or analysis actually distinguishes cyclic groups.

## What the published packages supply

Exact identities and imports remain in the [release catalog](PACKAGE-RELEASES.md).
Their native/JavaScript evidence does not establish Wasm or GPU implementations
of their underlying arrays, arithmetic, allocation or ownership operations.

| Existing component | Reuse in this plan | Boundary that remains missing |
| --- | --- | --- |
| [Vec](../packages/vec/INTERFACE.md) | Ordered field/layout tables, constructor descriptors, reusable queue/index metadata. | Elements must be `Data`; it cannot hold arbitrary owning `Type` payloads. Its affine container and native array lowering are not a portable runtime heap. |
| [IntMap](../packages/int_map/INTERFACE.md) | Type/binder/layout lookup, sparse usage or membership metadata, visited sets where appropriate. | Values are `Data`; no owning extraction or lifetime protocol. Fold order is low-bit-first, not numeric order; U32 count addition wraps. |
| [TermStore](../packages/term_store/INTERFACE.md) | Stable compiler AST/IR identities and serial memo states for analyses/lowering. | Data payloads, append-only slots and scope IDs; no reusable-slot generations, affine object fields, concurrent attempts or reclamation protocol. |
| [Symbols](../packages/symbols/INTERFACE.md) | Field, type and constructor spellings, with declaration IDs allocated in deterministic source order. | First-intern numeric IDs are not lexical identities, runtime capabilities, arena epochs or canonical cross-build names. |
| [Source](../packages/source/INTERFACE.md) | Origin spans and diagnostics for invalid declarations, bad layouts and unsupported constructs. | Scalar offsets and caller-managed file identity; no runtime addressing, byte decoding or heap validation. |
| [OutputBuilder](../packages/output_builder/INTERFACE.md) | Checked Wasm bytes, WGSL text, deterministic layout manifests. Existing compiler-private ULEB/nonnegative signed-LEB helpers remain usable. | Not a packed object buffer, checked record codec, general signed codec or allocator. |
| [Affine Slot probe](../research/adaptive-tasks/slot.bend) and [task/device protocol](../research/adaptive-tasks/DEVICE-PROTOCOL.md) | Seed contracts for put/take, suspension, logical destinations and phase-separated execution. | Slot is singular; device records are tree-shaped and never reused. Indexed owners, shared Data lifetime, generic captures and safe reclamation remain unimplemented. |

Wrapping an address in a `Data` record and putting it in Vec or TermStore does
not close these gaps. The object state and authority to transfer/drop its contents
must be specified and validated separately.

## Missing contracts and smallest acceptance probes

The probes below are **proposed**, not completed tests. Implement the independent
state/ownership model in Bend. Begin with a bounded sequential transition model
and generated Wasm. Qualify device layouts/lifetimes with focused device probes
alongside this work; later require the same observations from compiler-generated
WGSL. Handwritten qualification is not that final gate. Host code may dispatch,
decode and compare but must not implement the oracle.

| ID / missing contract or algorithm | Smallest useful acceptance probe | Semantic mutation it must reject |
| --- | --- | --- |
| R1: field projection and checked record layouts | A constructor with erased/live/erased/reusable fields projects declaration positions to `[none,0,none,1]`; retain all four type/quantity entries. Round-trip two distinct live values with an independent decoder. Include an inhabited mutually recursive Tree/Forest with Tip/Empty bases, an invalid live Type-in-Data twin, and checked offset/alignment overflow. | Store the erased field, swap live fields, infer field kind from its parent, or wrap an offset. |
| R2: indexed owning object storage | Two slots and distinct affine payloads 7 and 9. Insert, reject insertion into occupied/full storage while returning the unchanged store and incoming owner, take once, reject a second take, and explicitly drop the other payload. Capacity zero and one have real failure witnesses. Preserve unrelated slots. | Drop a rejected input, return a payload twice, mutate a different slot, or report exhaustion as a constructed value. |
| R3: reusable Data lifetime | Reuse a nontrivial immutable Data value in two live owners; release one, read the other, then release the last. Suspend one owner during the sequence. Include a Type object holding both an owned child and a reusable Data field. Copying and sharing representations may pass with different physical allocations, but the surviving value must agree. | Reclaim after the first release, duplicate an owning Type child, or permanently lose the last-release obligation. |
| R4: portable handles, freshness and ownership validation | Round-trip an explicit `(arena,slot,generation)` model through Wasm/WGSL-compatible words. Reuse one physical slot, then reject its old locator, a foreign arena and an out-of-range slot without modifying the new occupant. Use a tiny generation bound to force the declared exhaustion/retirement policy. | Ignore generation/arena, wrap a generation into an old valid identity, or treat a copied locator as a second extraction permission. |
| R5: captures and ordered joins | Capture two different affine values, a reusable Data value and erased metadata. Suspend/resume at budgets 0 and 1. Deliver right child 9 before left child 7; a noncommutative join returns 709. Reject duplicate delivery while preserving its rejected payload; completion consumes the join once. Add a late completion from a cancelled/replaced attempt. | Swap logical slots, copy an owned capture to both children, evaluate an erased capture, accept duplicate/stale completion, or execute a checkpoint twice. |
| R6: bounded frontier ownership and publication | Capacity 0/1/2; pushing to full returns the unchanged frontier and task owner. Transfer two tasks through ready/running/suspended/waiting states while reversing physical positions; their logical destinations survive. For the device refinement, one dispatch writes and the next reads; guard every word outside capacity. | Lose work on full, duplicate a task during compaction, change its destination, or consume a reserved slot before its payload is published. |
| R7: reclamation across suspension and readers | A two-object graph remains reachable only from a suspended frame or partially filled join. Attempt reclamation, resume and verify values. Cancel/drop, complete pending readers, then reclaim according to the candidate's policy. Exhaust a drop/trace work budget and resume from its retained worklist. | Omit a suspended/join root, reclaim while an old dispatch can read, forget work on budget exhaustion, or release an owned child twice. |

R1 must check addition, multiplication, alignment rounding, whole-record bounds
and decode tags before using offsets. Failed object construction either reserves
all required space before transferring inputs or uses an explicit rollback that
returns every input owner. Do not confuse this operation guarantee with rolling
back arbitrary source evaluation or effects.

R4's copied locator is not an unforgeable capability. Legal extraction must also
consume an owner or pass the store's state/transfer protocol. Object generation
alone does not distinguish cancelled task attempts: R5 needs an attempt identity
or an equally explicit ownership transition. Validate arena, bounds, allocation
state and generation before payload access; validate the expected layout/tag at
record-decoding boundaries. Never permit finite counters to
wrap into a retained identity. Retiring a slot or returning exhaustion is an
acceptable first policy; resetting a whole store needs a fresh noncolliding realm
or proof that old references cannot be presented again.

For R5/R7, distinguish logical drop from physical reuse. Affinity permits unused
values to be discarded; the runtime must account for that discard and its owned
children. This does not imply user-visible destructor/finalizer behavior. Rejected
insertion/completion retains ownership; cancellation must transfer or explicitly
drop each retained obligation. Interrupted cleanup retains both its remaining
worklist and the objects that worklist keeps alive.

The existing GPU probe's unique-parent retirement rule applies to a tree of task
obligations. It cannot reclaim a shared Data DAG. Preserve immutable phase inputs,
one writer per record and dispatch-separated publication until a stronger protocol
has its own evidence. A reservation counter is not publication of payload words.
Quiescence must cover every submitted reader, retained snapshot, suspended task,
waiting join and host-held reference before a backing object/buffer can be reused.

## Memory-management decision gate

Do not select a strategy from the phrase "affine language". The chosen design
must support **both** affine `Type` ownership and reusable `Data`, including their
coexistence in one object and in suspended captures. These are candidate
obligations, not a recommendation or an implementation choice:

| Candidate | Affine Type obligation | Reusable Data obligation | Additional acceptance condition |
| --- | --- | --- | --- |
| Regions/epochs or bounded arenas | Moves/extractions still invalidate prior owners; logical drop releases owned edges even if bytes are retained. | Every alias must remain within a live region, or an explicit escape/promotion mechanism extends its lifetime. | A region cannot end while a suspended frame, join or GPU reader retains it. Measure retained memory and explicit exhaustion; never silently abandon owners to reset an arena. |
| Unique Type objects plus reference-counted Data | Type payloads have one owning transfer path; dropping a Type object visits its owned children and releases its Data edges. | Every retained/shared Data reference has balanced acquire/release, checked count bounds and a defined last-release action. | Prove runtime cycles excluded or provide cycle handling; recursive datatype declarations alone settle neither. Establish GPU synchronization/publication and bounded resumable release cascades. |
| Tracing collection | Tracing does not enforce affine ownership; the checker/runtime must still prohibit duplicate extraction and account for logical drops. | Trace every live Data alias through accurate field descriptors and all task/host roots. | Establish safe points across device readers and suspended continuations. Moving storage needs stable indirection or complete relocation; handle freshness survives reuse. |

Data may instead be copied where the language permits. That choice must account
for copy cost, capacity failure and ownership of the resulting independent values;
it cannot be assumed cheap for recursive structures. A hybrid must specify which
representation each type/layout uses and how edges cross the boundary. Run R2,
R3 and R7 on the candidate before adopting it. No choice is made in this plan.

## Increment order, law quality and efficiency

1. Finish declaration/type/quantity metadata and R1's live-slot projection in the
   existing compiler. Specify versioned target layouts separately from source
   declaration order. Keep recursive kinds/name resolution independent from heap
   strategy.
2. Implement a bounded object/handle model and the R2–R4 witnesses, then compile
   one constructor/deconstruction/drop path to Wasm. Include explicit allocation
   failure and preserved ownership. Qualify handle/record encoding and lifetime
   premises against the device protocol now. Select a lifetime policy only after
   the decision gate.
3. Add structural recursion with explicit continuation/drop work and R5–R7.
   Keep the current independent evaluator and existing enum controls. Prototype
   finite storage first without presenting its size as a production heap bound.
   Exercise capture/join/reclamation device probes alongside this step; do not
   postpone the discovery of GPU-incompatible ownership until self-hosting.
4. Close the compiler's actual transitive implementation dependencies for Wasm
   A2/A3. Package availability under the seed is insufficient: arrays, numeric
   lowering, ownership, IO and the selected allocator need their target contracts.
   Runtime addresses, scheduling and allocation order must not enter emitted
   symbol/type/layout numbering. Require reproducible artifacts and independent
   positive, negative and exhaustion behavior for both generations.
5. After A2/A3, require the self-built compiler to lower the already qualified
   object/capture/continuation contracts into generated WebGPU adaptive tasks.
   Reuse the handwritten probe as a comparison, not as evidence of generated-device
   execution. Do not require
   physical scheduling or CPU/GPU transition counts to match unless specified.

For every probe, write the abstract state, legal transitions and public observations
before optimizing. Track each affine payload as owned by a caller, object, frame,
queue or join, or explicitly transferred/dropped; do not erase ownership evidence
through a contents-only projection. Track reusable Data reachability/lifetime
separately. Check composition and unrelated-state preservation, not just counts.
Use nonempty payloads, inhabited recursive bases and invalid-input neighbors.
Each proposed semantic mutant must still parse/typecheck and fail an independent
observation for its intended reason. See the [law-quality gate](LAW-QUALITY-GATE.md).

Keep type-level negative fixtures distinct from runtime stale-handle failures.
Quantified laws, bounded exploration, concrete normalizations and device runs
remain different claims. A constant success, always-empty store, reversed join,
or drop-all collector must fail the probe set. A zero-capacity failure law alone
does not establish useful storage. None of these proposed runtime probes has
been run by this documentation increment.

Efficiency targets need backend evidence: field projection should traverse the
descriptor once; indexed lookup/handle validation should not scan the whole heap;
captures cost at least their live contents; ordered-join slot insertion should
avoid scanning unrelated tasks. Allocation and reclamation costs depend on the
chosen policy. Dropping a recursively owned graph is not constant-time work.
Measure live/retired bytes, field/edge visits, reference operations and queue
occupancy on increasing inputs, with result agreement. A bounded cleanup step
must retain progress on exhaustion. Seed-native Vec costs do not prove generated
Wasm/GPU costs, and no runtime performance claim is made here.

## Evidence and ownership of this increment

This increment adds this plan and the thirteen-case reference receipt and links
them from the campaign notes. It changes no package, compiler or probe source.
Perch is not applicable: no owned executable declaration or law packet changed,
so no model request or semantic-pass claim is made. Runtime probes, policy
selection, compiled allocation and generated GPU validation remain future work.
