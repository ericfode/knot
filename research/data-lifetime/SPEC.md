# Data lifetime decision experiment (r3r7)

This is an executable policy model, not a compiler heap implementation. Source
quantities remain the checker's responsibility. No source profile is enlarged.
Expected transitions and costs are frozen before the Bend implementation in
`reference.py`, `traces.py` and `literals.json` (D7). The host model is independent
of Bend and is expressly a research oracle, not host implementation of Knot.

## Common contract

An immutable record has kind Type (0) or Data (1), a scalar tag, and zero to two
ordered child edges. Its payload occupies `2 + child_count` words: constructor
tag, scalar and child pointers. Zero denotes an absent edge; generated object
identities start at one and never repeat. Roots are named holder slots; frame,
join, caller and cleanup ownership are transitions of these holders. A record's
incoming obligations are roots, object edges and pending release work. Every
Type record has exactly one. Data cannot contain Type. Erased fields have no
edge. Construction can only point into older, immutable graphs: cycles cannot
be constructed. Mutation/backpatching is Unsupported.

Operations are transactional on failure, including counters and incoming roots:

- `alloc(dst, kind, tag, children...)` transfers distinct occupied roots into
  a fresh record; it needs a vacant destination and sufficient word capacity.
- `share(src, dst)` retains src and creates an independent holder in vacant dst.
  Sharing Type is Unsupported. **A** deep-copies every Data occurrence.
  **B** increments the Data root count; it does not visit its children.
- `take(src, destinations...)` consumes the parent holder, returning its ordered
  children. A unique parent releases its cell and transfers its edges. A shared
  B parent releases one reference and acquires one reference to each returned
  child, including repeated edges. Count overflow preserves the entire state.
- `move(src,dst)` transfers a holder, including into a suspended frame or join
  slot. Occupied-slot rejection preserves the incoming owner.
- `release(src)` moves its obligation to the cleanup stack. `clean(budget)`
  processes at most budget obligations. Last release frees a record and moves
  its child obligations onto that stack, in field order. A Type drop records
  its scalar serial exactly once. Budget zero/one retains all unfinished work.
- `pin(src,lease)` creates a non-owning read lease. Any outstanding reader
  blocks physical cleanup and take; allocation, share and logical release may
  proceed. `ack(lease)` permits reclamation only after the final acknowledgement.
  This deliberately conservative global barrier models dispatch completion.
- `cycle` is Unsupported without mutation. Missing/repeated roots, occupied
  destinations, kind violations and bad leases are Invalid **runtime requests**,
  not source-language judgements. Capacity/count/work limits are Exhausted.

Outcome wire codes: 0 Ok, 1 Invalid, 2 Unsupported, 3 Exhausted. Harness timeout
is separately `Exhausted host-timeout`; launch/IO errors are HostFailure; a
comparison failure is InternalFailure. Unsupported is not relabeled Invalid.
The protocol assumes valid internal records and bounded natural-number fuel;
it is not an untrusted-memory decoder or an arena/generation implementation.

For A, every physical record has one obligation. For B, Type stays unique and
Data has a bounded reference count including pending releases. B charges one
additional metadata word per Data record. Failed deep-copy reservation rolls
back its unpublished staging records. Last-release progress is required after
readers acknowledge and adequate cleanup budget is supplied.

## Fixed observations and measurement

After **every** command compare status, fresh identity, all record fields/counts,
root holders, pending work, leases, Type-drop serials and these counters:
allocations, frees, copied payload words, traversed edges (copy/take/cleanup),
RC acquires, RC releases, cleanup steps, live words, high-water words and maximum
pending cleanup obligations. Allocation initializes B's count to one; transfers
do not acquire. Failed transactions charge no committed policy work. Command
attempts are counted separately. Word counts exclude roots, worklists, allocator
metadata, staging space and host representation. They measure the candidate's
logical committed footprint, not process RSS, Wasm pages or complete CPU work.
Staging/descriptor/validation/lookup costs must be reported as emitter costs;
these counters cannot establish a runtime speedup.

Both candidates run the identical generated trees, lists, rebuilds and shared
subterm traces, plus literals for capacity, overflow, roots, cancellation and
reader barriers. The host model additionally checks graph/ownership invariants.
Every mutant must typecheck and execute; only an observation mismatch kills it.

`bench/` currently times Knot enum source compilation and nullary Wasm exports.
It cannot run these seed-built generic store models or sample heap counters.
Use the common trace/counter gate here; integrating a stateful runtime workload
and these counters into `bench/` follows emitter integration. No timing claim.
