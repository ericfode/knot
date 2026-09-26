# Execution-model laws for Knot

Status: adaptive continuation tasks selected by the user on 2026-09-26.
Wasm is selected; GPU execution is required. The laws below are the working
specification for that model. A bounded affine protocol and WebGPU tree probe
now have [checked/executed evidence](../research/adaptive-tasks/README.md).
Detailed production scheduling, representations, and full refinement remain open.
Read the [case for the choices](EXECUTION-MODEL-CASE.md) alongside these laws.

## Domain and observations come first

The initial runtime domain is the checked, erased, strict affine core: closed
programs using constructors, exact U32 operations, case analysis, permitted
sharing of `Data`, closures, explicit calls, and pure fork/join. Use the pinned
reference's primitive behavior, including wraparound and exceptional operands;
do not silently substitute Wasm trap behavior for Bend operations.

For progress claims, restrict to well-founded computations in this supported
core, a fair scheduler, and sufficient storage. `unsafe`, foreign effects,
divergence, unsupported primitives, and allocation failure do not satisfy those
premises. These restrictions are substantive: the witnesses below include
nonempty forks with unequal values, dependent continuations, and finite work.
Floats need a separately chosen cross-backend contract; exact reassociation is
not a default law. Type-checker normalization is a separate execution problem.

An observation is a structural value, or a host-effect trace and final value.
Heap addresses, task numbers, and queue order are not source observations.
Compare heaps modulo a bijection of fresh identities that preserves edges and
ownership. Debug traces and timing are separate observations used to inspect
cost; do not demand identical debug traces from different schedulers.

Distinguish `Finished(value)`, `Yield(checkpoint)`, `Exhausted(kind)`,
`Fault(kind)`, `Cancelled`, and `Unsupported(capability)`. A resumable exhaustion
variant must explicitly return a valid checkpoint; resumability is not implied
by the word exhausted. Never turn missing capacity or GPU capability into a
successful result. Successful pure results can be schedule invariant while
peak memory and exhaustion are schedule dependent.

For a target state `m` and source/reference configuration `c`, let `R(c,m)` mean
that the representation denotes the same residual computation, values, and
owned resources. It must account for queued work, running work, suspended
frames, join slots, shared values, and pending host requests. A relation on only
the ready queue is too weak: losing a suspended continuation would be invisible.

## Common laws

**E1 — semantic refinement.** If `R(c,m)` and a target transition succeeds from
`m` to `m'`, there must be zero or more reference transitions from `c` to `c'`
with `R(c',m')`, preserving the observable effect prefix. Administrative steps
may stutter, but cannot stutter forever while enabled source work remains.
Conversely, under the progress premises, enabled reference work can eventually
be simulated. This rules out both wrong answers and a scheduler that does
nothing forever. A proof for a particular lowerer must instantiate `R`.

**E2 — affine ownership.** Each live mutable payload has exactly one owning
location: an active register/frame, an owned store slot, a queued record, or a
join result slot. Moving changes that location and invalidates the old one.
Dropping can destroy it; cloning cannot create a second affine owner. Reusable
immutable `Data` can have explicit sharing obligations, which must be discharged
before reclamation. Numeric IDs are references, not evidence of ownership.

**E3 — independent-step commutation.** If two enabled pure steps have disjoint
mutable footprints and neither produces a value needed by the other, executing
them in either order produces related states, modulo fresh-ID renaming. Common
read-only data is allowed while its lifetime is protected. Allocator/refcount
operations may need their own linearization argument; disjoint source variables
alone do not make concrete memory accesses independent.

**E4 — scheduling transparency.** For a terminating pure program, two fair,
refining executions that both finish under sufficient resources have the same
structural result. This is a proposed consequence of E1–E3 and progress, not a
proof already supplied by Bend's type checker. It says neither equal time nor
equal memory. It does not allow inventing parallelism across effect dependencies.

**E5 — fork partition.** A fork partitions its affine captures among children
and the saved continuation. A child gets each owned capture at most once;
permitted `Data` sharing is explicit. Every child is assigned a logical result
slot before scheduling. Scheduling two children sequentially remains a valid
implementation of a pure fork's value semantics.

**E6 — join protocol.** For child results `a` and `b`, delivering left then
right or right then left yields `(a,b)`. The slots are source ordered, not
completion ordered. A slot changes from empty to filled at most once. A join
becomes runnable only when all its slots are filled; its continuation is
consumed at most once. Duplicate deliveries are rejected without overwriting
the earlier result. For affine payloads, rejection must return the rejected
payload or explicitly dispose of it according to the ownership contract.

**E7 — work conservation.** At each transition every live continuation/task
obligation is represented exactly once among ready, running, suspended, or
awaiting-result states. Fork replaces a parent with its children and a waiting
join; it does not preserve an executable copy of the parent. Return retires a
child and supplies exactly its designated result. Queue compaction/reordering
preserves the multiset of obligations and all destination slots.

**E8 — bounded suspension.** A yield occurs at a documented safe point with all
live registers, frames, destinations, and ownership recorded. Resuming cannot
repeat effects or lose work. For a deterministic reference transition function,
`run(n+m,s) = resume(m,run(n,s))`, with terminal states absorbing, when fuel is
the same logical-step measure and no external events intervene. Changing a
real scheduler's quantum may change its internal state and cost; E4, rather
than literal checkpoint equality, is the cross-scheduler requirement. Long
primitives must themselves be chunkable or have an explicit maximum cost.

**E9 — effects and cancellation.** Pure device work produces values or requests;
the host executes effects in their declared dependency order. An effect request
is applied at most once when suspending/resuming. A cancelled computation cannot
publish a success, and its resources cannot be reused until outstanding device
work can no longer access them. This is an in-process protocol, not a promise
of exactly-once external I/O across host crashes.

**E10 — explicit resource behavior.** Bounds checks precede address arithmetic,
reservation, and writes. Failure cannot wrap an index, overwrite another task,
partially lose an affine value, or fabricate completion. A claimed recoverable
failure leaves a valid checkpoint or returns the still-owned inputs. A fail-stop
profile instead owns the whole arena until quiescent cleanup. Choosing between
these profiles is part of the ABI; mixing them is unsound.

**E11 — representation and erasure.** For supported values,
`decode(encode(v)) = v` modulo representation identities, with explicit widths,
alignment, endianness, tag ranges, and overflow behavior. Erasure preserves the
chosen runtime semantics only after checking its proof/type premises. An erased
proof does not establish that the generated allocator or scheduler refines it.
Host pointers are not GPU addresses; a 64-bit upstream term is not a portable
WGSL value layout. `Data` stored in several places still needs a lifetime rule.

## Model-specific obligations

| Model | Required additional law | Witness / counterexample that matters |
|---|---|---|
| Sequential stack/continuation machine | Push followed by a result return restores exactly the saved environment and next instruction; tail calls do not add a continuation. | `f(x) + g(y)` where `f` nests calls and the two results differ; saving only the program counter loses captures. |
| Fixed fork/join placement | Placement is a total, single-valued assignment for each task and preserves E7. Equal work is a performance precondition, not a consequence of ownership. | Fork subtrees of equal node count with unequal per-node work. The program is valid even when one lane runs much longer. |
| CPU work stealing | A successful steal transfers one executable task to one owner; competing steals cannot both win. Publication and reclamation obey the selected CPU/Wasm memory model. | Owner pop racing two thieves on the final deque item; wraparound and stale slots. A sequential deque proof does not cover this. |
| GPU phases with movable continuations | Phase input is immutable/owned by its consumer; each output region has one writer; phase exchange preserves E7 and publishes payloads before consumers read them. | Complete right before left, compact their records, then join in logical slot order. Move a suspended task with live affine captures. |
| Bytecode machine | Each verified opcode/operand layout simulates a reference transition sequence; invalid tags/offsets fail explicitly. | Bad instruction tag, truncated capture vector, changed arity. Interpreter dispatch is orthogonal to scheduling. |
| Specialized Wasm/WGSL | Each generated control edge and layout has the same refinement relation as the bytecode form. | Save/reload across a branch, non-tail recursive return, uncommon constructor arm. Specialization cannot erase a needed continuation. |
| Interaction nets | The Bend encoding/readback preserves values and allowed sharing; rewrites preserve interface/wiring; enabled redexes cannot be reduced twice. | Fan/duplication, erase, and closure-capture interactions with aliasing. Confluence of a net calculus alone proves none of the encoding or physical publication laws. |
| Array/data-parallel lowering | Pure map fusion preserves order; reduction rebracketing requires an associative operation and identity in the actual primitive semantics; flattening preserves segment boundaries. | `map f (map g xs) = map (f ∘ g) xs`; use subtraction to kill an invalid reduction rewrite and empty segments to kill incorrect offsets. |
| Demand/lazy graph evaluation | Thunk states are explicit, updates are single-assignment, and readback preserves the chosen demand semantics. Relating it to strict execution needs a separate domain argument. | An unused expensive argument, a shared demanded expression, and a re-entered thunk. Budget/exhaustion behavior need not agree with strict execution. |

The map-fusion equation assumes pure total functions and compares values, not
allocation-failure behavior. Reusable function syntax in that mathematical
statement is not permission to duplicate an affine closure in generated code.

## The WebGPU publication obligation

WGSL atomic built-ins have relaxed semantics. Its synchronization built-ins
operate at workgroup scope. Thus this attempted cross-workgroup argument is
invalid: “write ordinary payload; increment an atomic ready counter; any lane
observing ready can read the payload.” Atomic ownership of a counter and
visibility of unrelated payload words are different obligations.
See [WGSL memory semantics][wgsl] and [synchronization][wgsl-sync].

**G1 — phase publication.** A consumer of cross-workgroup output runs in a
subsequent ordered dispatch with the appropriate WebGPU resource usages. Within
the producer dispatch no invocation reads another workgroup's newly published
ordinary payload. WebGPU defines a usage scope per dispatch; its implementation
performs the inter-dispatch resource synchronization. See the [spec][webgpu]
and the [GPUWeb maintainer explanation][dispatch]. A workgroup-local optimization
needs its own uniform-barrier argument.

**G2 — allocation is not publication.** An atomic reservation may assign
disjoint output ranges, provided arithmetic cannot wrap and capacity is checked.
The reserved slot is not a readable finished record during that dispatch.
Capacity failure returns owned pending work or enters explicit fail-stop; an
unbounded fetch-add with a post-hoc bounds test is not sufficient on wraparound.

**G3 — phase-safe join/reclamation.** During a work phase, child writers can
fill distinct preassigned result slots. A later join phase reads them and has
one invocation own each join decision. A later work phase consumes the resulting
continuations. Storage reclaimed for sharing or suspended frames cannot be
reused until its readers are quiescent. Delaying joins or frees changes cost,
not E6. A same-dispatch fast path needs a stronger, separately verified protocol.

**G4 — portable progress.** No kernel spins waiting for another workgroup to
run. A bounded quantum produces completion, a checkpoint, or an explicit
resource outcome. Each dispatch is finite under the supported primitive bounds.
This design avoids relying on simultaneous residency of all workgroups.

These remain general proof obligations. The bounded WGSL tree probe implements
dispatch-separated publication, unique writers, guarded frontier reservation,
and retirement; its [protocol argument](../research/adaptive-tasks/DEVICE-PROTOCOL.md)
and device tests are narrower evidence, not a mechanized weak-memory proof.
The abstract Bend join below does not model weak memory.

## Cost laws and limits of a semantic prediction

Let `W` be source work in an explicitly chosen primitive-cost model and `S` its
dependency span. With `P` ideal processors, time is at least `max(W/P,S)`.
This is a lower bound, not a scheduler implementation or GPU performance result.

A full binary reduction of depth `d` admits a sequential depth-first evaluation
with O(d) pending frames, while eagerly materializing its whole leaf frontier
requires O(2^d) pending leaf records. Assume the input is generated from depth
and index, and leaf work/result size is constant; do not count an already
materialized input tree as new scheduler storage. This is a concrete reason
not to promise schedule-independent bounded-memory success.

For fixed task assignment with indivisible costs `w_i`, the slowest assigned
lane controls the end of the phase. Redistribution cannot shorten one opaque
100-unit task. It can help only if that task exposes independent descendants
or a movable continuation with useful remaining parallelism. Time slicing a
serial dependency chain improves responsiveness, not its span.

Map fusion removes an intermediate array of size `n` and its corresponding
write/read traffic under the stated domain. This is a stronger semantic cost
argument than “a clever scheduler will be fast.” Conversely, neither stronger
confluence nor fewer beta reductions implies fewer device memory transactions.

## Checked evidence and still-open proof work

The [Bend model](../research/execution-models/model.bend) gives all transitions of
a binary join over arbitrary `Data` payloads. [LAWS.bend](../research/execution-models/LAWS.bend)
states 18 equations; [PROOF.bend](../research/execution-models/PROOF.bend) proves
them by definitional equality. The equations cover all five control states,
both delivery operations, completion-order independence, and a second take.
Payloads remain universally quantified; these are not only closed numeric tests.
They are local transition/composition theorems, not an induction over arbitrary
execution traces or a proof of an optimized implementation.

In particular, the second-take equation threads the returned state. This
copyable `Data` model does not stop a client from retaining and reusing an older
ready snapshot. A concrete implementation needs E2's single-owner discipline
to turn that state-machine rule into a global one-time-consumption guarantee.

The inhabited runtime witnesses use distinct U32 values 7 and 9, plus 0 and
4294967295. Ten observations agree between the reference JS backend and native
C output. Four changed models still typecheck but fail the laws and change a
runtime witness: swapped result slots, overwritten duplicate, repeated take,
and premature completion. See [the receipt](../research/execution-models/evidence.json)
and [reproduction instructions](../research/execution-models/README.md).

The [new affine protocol](../research/adaptive-tasks/README.md) closes a narrower
part of E2/E8: generic owning-slot transitions, complete zero-fuel state
preservation, and arbitrary-budget composition. It adds captured unary/binary
frames and quantity rejection controls. Its WGSL counterpart passes 38 finite
hardware runs against independently evaluated Bend trees, with explicit bounds
failures, logical-worker redistribution, and retired child slots. Five Bend and
three device semantic mutants are rejected.

Open: general E1–E11/G1–G4 refinement, arbitrary concurrent histories, n-ary
joins, generic indexed affine storage, reusable allocation, sharing,
failures/cancellation, and source compilation. There is no full-runtime
verification or scheduler-performance claim. The Bend checker, Base primitives,
upstream compilation paths, and device implementation remain trusted tools.

[wgsl]: https://www.w3.org/TR/WGSL/#memory-semantics
[wgsl-sync]: https://www.w3.org/TR/WGSL/#synchronization-builtin-functions
[webgpu]: https://www.w3.org/TR/2026/CRD-webgpu-20260915/#synchronization
[dispatch]: https://github.com/gpuweb/gpuweb/discussions/4434
