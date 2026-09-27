# Flat store execution contract

This increment lowers the bounded indexed store's word-payload transitions into
an actual Wasm module emitted by Bend. It supplies a runtime building block for
structural field lowering. It neither changes Knot's accepted source profile
nor claims self-hosting or compilation of arbitrary Bend to GPU code.

The independent oracle is the existing Bend Data-list model. Host code may
provide command words, invoke exports, inspect linear memory and compare with
Bend-generated observations. The host implements no store transition or oracle.

## Scalar word layout

All words are U32. Wasm memory accesses use little-endian bytes; a future WGSL
storage buffer uses `array<u32>`, not `array<vec3<u32>>`. Locators occupy three
adjacent words `(arena,slot,generation)` with no implicit vector padding.

The header has eight words: arena, logical capacity, generation ceiling,
free-chain head, result slot, result generation, result value, disposer count.
`0xffffffff` marks the end of the free chain or an absent result locator.
Each cell occupies four words: state (0 vacant, 1 live, 2 retired), generation,
payload serial and next free index. Cell i starts at byte `32 + 16*i`.
Capacity is 0..4096. Bounds are checked before this arithmetic; the largest
addressed byte is 65567. The Wasm module reserves exactly two 64-KiB pages and
does not grow memory. Padding after the logical cells must remain untouched.

Vacant cells have zero payload and their ordered free-chain link. Live cells
have their payload and a sentinel link. Retired cells retain the ceiling
generation, have zero payload and a sentinel link. The abstraction observes
every logical cell, generation, free-list order and returned/disposed word.
It ignores unused backing bytes except the separate canary assertion.

## Operations

Each module instance starts uninitialized. `init(arena,capacity,ceiling)` accepts
one successful initialization; subsequent init calls fail without modifying any
byte. Capacity rejection also preserves memory. The fixed backing reservation
occurs at instantiation, before init; rejection precedes logical initialization,
not the host engine's backing allocation. The caller supplies globally fresh
arena IDs across contexts whose locators might meet.

`put(index,value)` and `alloc(value)` return a status. Success writes the allocated
slot/generation and zero result value. Rejection writes absent locator words and
returns the incoming value; logical store state is unchanged. Initial allocation
order is increasing. Put unlinks its explicit slot, preserving the other free IDs.

`take(arena,index,generation)` validates arena before bounds, then occupancy and
generation. A live matching cell transfers its word once. Below the ceiling it
becomes vacant at generation+1 and prepends to the free chain. At the ceiling it
retires permanently. Success returns the original locator words and payload.
Failure returns absent locator words and zero value; logical store is unchanged.
Retired returns Retired regardless of the requested generation; vacant returns
Vacant for a matching generation and Stale otherwise.

`release` uses take, then invokes the fixed word-disposer witness on success.
The witness returns the same serial and increments a U32 modular count once.
Failure does not increment. This observes a disposer call; it is not generic
recursive destruction or physical reclamation of an arbitrary Type graph.

Statuses are 0 success, 1 Limit, 2 Full, 3 Bounds, 4 WrongArena, 5 Stale,
6 Vacant, 7 Occupied, 8 Retired, 9 NotInitialized, 10 AlreadyInitialized and
11 Corrupt. Pre-init operations return NotInitialized without touching memory.
Other operation failures may change only the result registers, not store fields.
Corrupt is an internal invariant failure, distinct from source rejection and
resource exhaustion. Bounded free-chain traversal cannot spin indefinitely.

## Ownership and trust boundary

The module serializes access to one mutable store. Duplicate locators cannot
extract a current occupant twice. Host calls and exported memory are privileged;
this is not a sandbox against a host that writes forged cells, clones a module's
memory or reuses an arena ID. Only init and the declared operations construct
normal states. Near-ceiling runtime witnesses may install an explicitly valid
internal state to avoid billions of setup cycles. Corrupt checks are defensive,
not a complete validator for arbitrary hostile memory images.

Payloads in this probe are words standing for owners. The seed CPU component
already checks generic Type transfer; representation refinement for nested
objects, reusable Data, captures and suspension remains required. No CPU timing
or Wasm success establishes a GPU publication or reclamation protocol.

Acceptance requires actual module validation/execution, exact agreement with the
independent Bend model, boundary/canary and lifecycle negatives, byte-identical
native/Bun emitters, complete proof and trust inventories, and semantic mutants
that still emit valid executable modules. Field projection and full Wasm tree
programs remain subsequent compiler integration gates.
