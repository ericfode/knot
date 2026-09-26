# Execution-model requirements for the package builders

Research handoff, 2026-09-26, from Compiler Planning to **Survey Bend compiler
support** (`01a0ded6-ed33-72d2-a28e-e84b2895faaa`). The user authorized this
coordination. The coordinator owns package assignments and campaign records;
this document does not reassign another chat's files or expand a package release
silently. Research artifacts are owned here under `research/execution-models/`
and `research/adaptive-tasks/`.

Decision update, 2026-09-26: the user selected **adaptive continuation tasks**.
Prioritize the owning slot store, continuation/join records, and bounded frontier
as dependencies of that selected model. Fixed placement remains a comparison
baseline; interaction-net machinery is outside the chosen implementation path.
The first tree-task phase protocol now has finite hardware evidence; production
scheduling, generic storage, and full refinement still require validation.

Read [the model comparison](EXECUTION-MODEL-CASE.md) and
[the laws](EXECUTION-MODEL-LAWS.md). P0 means needed for a narrow semantic/device
prototype; it does not mean all items must enter the six current releases.

## Executable handoff: 2026-09-26

The [adaptive-task probe](../research/adaptive-tasks/README.md) is implemented.
Reuse its contracts and independent oracle, with these exact limits:

- `Slot<A:Type>` has `put`/`take`; rejection returns both existing slot and
  uninserted owner. `Task`, `Frame`, `Payload`, and `Run` are affine. Twelve laws
  check, including arbitrary-budget composition; invalid reuse is rejected in
  the quantity phase. This is one slot, not an indexed arena or stale-ID proof.
- Continuations preserve logical destination, remaining work, and owned
  captures. The prototype's binary operation is noncommutative, so reversed
  arrival/order bugs cannot hide behind addition. Keep that witness in package
  refinements. Generic failure/drop obligations remain additional contracts.
- The GPU uses 48-byte operation/64-byte task records and an immutable prior
  snapshot, unique work-record owners, then a separate join/retirement phase.
  Parent capture and child invalidation use the same immutable snapshot. This
  requires exactly one parent per child; do not apply it to shared DAG nodes.
- Frontier atomics reserve distinct bounded positions; reservation is not
  payload publication. Preserve task destination and logical slot through
  compaction/reordering. The next dispatch consumes the finished frontier.
- Slots are never reused within a run. Lifetime ends after queue quiescence.
  Reusable handles need arena/generation validation and wrap policy; sharing
  needs its own lifetime protocol. None is supplied by the prototype.

The receipt has 38 Metal runs, explicit capacity 0/1 and round/quantum outcomes,
five Bend and three device semantic mutants. It is feasibility evidence with
handwritten WGSL and a native Node host. This does not expand any published
package contract or resume the paused package campaign. Next package work is
an indexed owning store, lawful bounded frontier, and generic continuation/join
storage; the coordinator retains assignment and release ownership.

## Existing packages: interface requirements

| Package | Need | Laws / constraints | Priority |
|---|---|---|---|
| Vec | Ordered immutable syntax, instruction, layout, and frontier metadata; bounded append/slice. | Current `T: Data` restriction is appropriate. Preserve the owner-threading API and unchanged-state failure. Do not claim it stores affine closures/handles safely just because an ID fits in U32. | P0; preserve current scope. |
| TermStore | Stable arena-scoped syntax/IR identities; memoized transformations; deterministic traversal. | IDs stay valid for documented arena lifetime. Distinguish missing/pending/ready/failed states; resource exhaustion is not a computed term. Never reuse a live ID while a continuation/device record can refer to it. Reuse later requires generation/lifetime validation. Keep immutable compiler terms separate from a mutable runtime heap. | P0 for compiler IR; runtime store is a separate component. |
| IntMap | ID→layout, definition→code tag, free-variable sets, worklist membership, memo states. | Lookup/update preservation, overwrite behavior, absence versus present sentinel, explicit bounds. Iteration order must be specified or sorted before deterministic emission. | P0. |
| Symbols | Stable symbols within a compilation, deterministic serialization/remapping across builds. | Equal source names in the same namespace map consistently; namespace distinctions survive. Allocation-order IDs must not leak nondeterministic artifact order. | P0. |
| Source | Origin spans for unsupported constructs, primitive restrictions, allocation/stack errors. | Span identity survives lowering; preserve logical source origin through generated continuation tags. Byte/codepoint indexing must be explicit. | P0. |
| OutputBuilder | Wasm byte output, WGSL text, layout/entry-point manifest. | Use the published distinct text/raw-byte paths and checked byte capacity. Separate unsigned/signed LEB128 algorithms still need canonical roundtrip and boundary witnesses. | P0; consume the existing byte API before adding codecs. |

The published working Vec interface limits length to 16,777,216 and accepts
reusable `Data` elements. That is an inspected interface constraint, not a
verified Wasm/GPU capacity or performance claim. Query its owner before deriving
runtime buffer limits from it.

## New components: bounded contracts to begin now

### P0: owned slot store and generation/lifetime discipline

An owning store must support payloads that cannot be copied. `put` transfers a
payload into an empty slot; `take` transfers it out and invalidates the slot.
Read-only handles may be copyable, but cannot independently authorize repeated
extraction. A failed insertion returns the still-owned payload. A failed take
leaves state unchanged. Fixed never-reused slots are an acceptable first model;
avoid pretending reuse is harmless. Later `(arena, slot, generation)` handles
must reject old generations, with an explicit wraparound policy.

Required witnesses: two takes of one slot; wrong arena; out-of-bounds slot;
failed put preserving input; reuse with a stale handle. Abstract laws E2, E10,
E11. Compiler TermStore IDs and runtime owning handles have different contracts.

### P0: bounded frontier/queue

Start with a sequential functional contract for a bounded FIFO or ordered
frontier: empty, singleton, push/pop, full/empty failure with unchanged state,
and wraparound if using a ring. Queue length/content must refine an independent
list model. Moving a record conserves its task obligation exactly once (E7).
Queue FIFO ordering is a useful package contract; program result order still
comes from logical join slots and cannot depend on FIFO completion order.

For the first GPU version, phase input is immutable and phase output has one
writer per assigned region. This does not require a persistent MPMC GPU queue.
If reservation atomics are added, prove bounded nonoverlap and no index wrap;
reservation does not publish ordinary payload data (G1–G2).

### P0: continuation and binary-join records

Continuation record: code tag, captured environment, local frame/checkpoint
state, and parent destination. Result destination: owning join identity plus
logical slot. Binary join states: open, left-only, right-only, ready, taken;
extend to n-ary only with explicit slot/remaining-count invariants.

The [reference model](../research/execution-models/model.bend),
[18 checked laws](../research/execution-models/LAWS.bend), and
[evidence](../research/execution-models/evidence.json) are available to reuse as
an abstract contract. Distinct payloads and reversed arrival order are essential
witnesses. It is a **sequential Data-payload model**; a store of actual affine
environments and a concurrent device implementation need separate refinements.

For WGSL, do not implement “ordinary slot write, relaxed countdown decrement,
last child immediately reads all slots” across workgroups. Start with result
writes in one dispatch and a single owner per join in a later dispatch. No
in-kernel spin waiting for another workgroup. The native reference runtime's
Metal/CUDA fences are not portable WGSL built-ins.

### P0: checked layout and byte algorithms

Provide integer `checked_add`, `checked_mul`, and alignment/range validation for
buffer sizes/offsets. Failed reservation must not consume an affine input.
Roundtrip values across explicit record layouts; reject unsupported tags and
truncated records. Prefer U32 fields/offsets initially and account explicitly
for any wider source primitive. Never copy host pointers into GPU storage.

For Wasm integers, canonical ULEB/SLEB encoding needs decode/encode laws and
witnesses crossing 7-bit group boundaries, extrema, and signed sign-extension
boundaries. Do not encode Wasm bytes through Unicode codepoint operations.
The published OutputBuilder already has a checked byte path; LEB codecs and
record-layout algorithms remain separate work. See [the release catalog](PACKAGE-RELEASES.md).

### P1: scan, stable compaction, partition, and retirement

Exclusive scan over bounded counts assigns disjoint output ranges. Prove
`offset[0]=0`, adjacent offsets differ by the preceding count, final extent is
the total, and overflow is rejected. For stable compaction, output equals the
input subsequence satisfying the predicate: no lost, duplicated, or reordered
records. Program correctness may allow record reorder; stable compaction makes
the storage contract and debugging simpler.

Partition by code tag is a possible divergence optimization; destination IDs
must survive it unchanged. Retired records are reusable only after all relevant
phase readers complete. Shared immutable `Data` needs a lifetime protocol too;
delaying reclamation trades synchronization for retained memory.

### P1: compiler analyses and lowering algorithms

Keep transformations individually observable: free-variable analysis, closure
conversion, administrative/call normalization, defunctionalization of saved
continuations, fork/capture partition, and effect-dependency analysis. These
need deterministic sets/maps, explicit worklists, and origin-preserving IDs.

Reachability and monotone fixed-point analyses should terminate on a stated
finite graph/lattice and produce the least intended result. Strongly connected
components are useful for identifying recursive groups/cycles and issuing
precise profile errors, even if the first source subset rejects those cycles.
Topological order alone cannot be used on an unchecked potentially cyclic graph.
Binder substitution/renaming requires capture-avoidance laws; numeric node-ID
equality is not a substitute for binding identity.

### Deferred unless an experiment earns them

Persistent CPU work-stealing deques, general GPU concurrent maps, all-atomic
publication protocols, graph/net redex schedulers, and a full segmented-array
optimizer. Each has additional proof and representation costs. A regular
array-kernel path will later need lawful map/reduce/scan, shape descriptors,
segment offsets, and explicit associativity contracts.

## Acceptance and ownership of evidence

Use the shared [law quality gate](LAW-QUALITY-GATE.md). A sequential model may
be useful immediately, but publication must describe the exact model,
implementation, and backend scope. Native Bend results establish neither Wasm
behavior nor GPU memory safety. Kill semantic mutants that still typecheck;
record payload/domain witnesses and source hashes.

The coordinator should route these contracts to the six existing owners and
decide which additional components get their own build work. Research will
provide narrowed contracts and findings; package owners retain implementation,
proof coverage, and release responsibility.
