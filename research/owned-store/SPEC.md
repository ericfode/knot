# Bounded indexed owning store

This is the R2/R4 qualification component for the structural Wasm runtime.
It is implemented in Bend under the seed before lowering the same ownership
transitions into Wasm. It does not select a general Data reclamation policy.

An affine `Store<A:Type>` owns every occupied cell. A reusable locator contains
three U32 words `(arena,slot,generation)` and carries no extraction permission
by itself. Every operation consumes the current store and returns its successor.
A successful take removes the payload once. Copied locators cannot take from an
old store after that affine store has been consumed.

The store has fixed logical capacity 0..4096 and generation ceiling 0..U32.max.
Physical backing may round up to a power of two; padding is never addressable.
Fresh cells have generation zero. Releasing generation g below the ceiling
makes that slot vacant at g+1. Releasing the ceiling generation retires the
slot permanently. No generation addition executes at the ceiling; IDs cannot
wrap into validity. Retirement reduces future usable capacity explicitly.

The caller supplies an arena ID. All simultaneously compared stores and all
subsequent stores whose locators may survive must have distinct arena IDs.
A production realm allocator and serialized restore policy remain a separate
required contract; this component does not claim global uniqueness of supplied
numbers. Internal constructors/backing arrays are not public construction APIs.

`new(arena,capacity,ceiling)` fails Limit before allocating above 4096.
`put(store,index,value)` inserts into a vacant logical slot and returns its
locator. Bounds, occupied and retired failures return the unchanged store and
incoming owner. `alloc(store,value)` chooses the first entry of the explicit
free list; full/retired capacity returns Full with both owners preserved.
`take(store,key)` validates arena and logical bounds before cell access. Live
and vacant cells validate their generation; retired cells always return Retired.
Failure preserves every cell. Success returns the payload and successor store.
`release(store,key,dispose)` uses the same take transition and applies the
caller-supplied disposer exactly once on success; failed take never calls it.
Its result is an observation of disposal, not a proof of physical reclamation.

Free-list order starts at increasing slot indices. Explicit insertion removes
that slot without reordering unrelated free entries. Take adds a reusable slot
at the front; retired slots never reenter it. This is deterministic allocation
order, not a source-language observable or a proposed final runtime ABI.

An independent Data list model tracks cell tags, generations, payload serials
and observations for finite traces. Actual store payloads remain Type. The
abstraction compares arena/capacity/ceiling, every cell including vacant/retired
ones, free-list order, rejected inputs and taken/disposed outputs. A contents-only
projection is insufficient. Exact snapshots consume the store, never clone it.

The implementation uses checked indices before Array.swap/set. A temporary
retired cell may replace a target only within one synchronous operation; the
original or successor cell is restored before returning. Raw Array helpers mask
indices and are not validation. Indexed operations use the array backend;
explicit put removes one ID from a bounded list, alloc/take use its head.
No constant-time claim includes payload destruction, initialization or snapshots.

No Wasm/GPU store, shared Data lifetime policy, suspension-safe reclamation,
concurrent mutation, asynchronous readers, generation reset or cross-realm
serialization is established by seed CPU tests. R1 layouts and R3/R5–R7 remain
separate qualification gates alongside compiler integration.
