# Owned Wasm heap: bounded law review

Contract: [SPEC.md](SPEC.md), [compiler profile](../../src/SPEC.md), and the
[D10 lifetime packet](../../research/data-lifetime/README.md). Implementation:
[heap.bend](../../src/heap.bend), encoded by
[heap-code.bend](../../src/heap-code.bend). Source ownership lowering lives in
`src/owned.bend` and `src/ownership.bend`; their checker/liveness obligations are
separate from the runtime kernels reviewed here.

The mechanism keeps one physical cell per immutable object, with one incoming
obligation for Type and a count of incoming obligations for Data. Incoming
obligations are source holders, object edges, and pending release work. Opening
a unique parent moves its fields and frees that parent. Opening shared Data
acquires each returned pointer field, including repeated edges, then decrements
the parent. All child increments are checked before any is published. Scalar
and erased fields never acquire or release a pointer.

## Physical contract

The module owns exactly two fixed Wasm pages (131,072 bytes), with no imports or
memory growth. Bytes `[0,16384)` hold 4096 free-list heads indexed by live-slot
count. Bytes `[16384,49152)` hold 4096 eight-byte release frames. The heap is
`[65536,131072)`; the remaining 16 KiB are reserved and unused. These reservations,
the three prefix words per cell, and fixed page size are physical costs. Logical
freeing permits reuse; it does not reduce the Wasm reservation.

Payload pointer `p` still addresses `[tag][live slots]`. Prefix words at
`p-12/p-8/p-4` are state, count/free-next, and layout identity. States are 0 free,
1 live, 2 dropping. A live Type count is exactly one. Data counts are positive
and bounded by the configured ceiling, initially 2147483647. A free cell uses
its count word as its next pointer. Allocation removes the exact size-class
head or advances the checked bump, then installs state 1/count 1/layout. Free
publishes the old class head in the freed cell before changing that head. Classes
are neither split nor coalesced; incompatible free cells can coexist with
Exhausted allocation.

A release frame is `[pointer,cursor]`. Cursor zero owns one release obligation.
Cursor `k+1` means the dropping parent owns the unvisited fields from live slot
`k`. The collector uses an explicit Wasm loop. It decrements a shared count, or
marks a last-reference cell dropping and scans one slot per quantum. A child is
queued before the parent cursor advances. A full stack returns Exhausted without
advancing that cursor. A parent is recycled only after its fields have been
scanned. Thus partially completed cleanup preserves a resumable ownership path.
The packet's model frees parents eagerly and uses one obligation per quantum;
its intermediate work counts are not claimed equal to this cursor machine.

The default 4096-frame reservation covers the physical heap: every cell is at
least 16 bytes, and each extra path edge requires a parent with a live pointer
slot (at least 20 bytes). The largest one-child chain that fits is 3277 cells.
The component gate constructs that chain and drains it without recursive Wasm
calls. Debug limits deliberately make smaller stack/count bounds observable.

## Public operations and evidence

Runtime exports are debug/test capabilities, not an untrusted host object API.
The compiler's checked calls use these same operations.

| Operation | Obligation | Checked equations / independent execution |
| --- | --- | --- |
| `__heap_alloc(layout)` | Size-class reuse or bounded fresh allocation; starts count 1 | Seven semantic allocator laws; 12 complete allocator-model snapshots; exact-class reuse and full-heap unchanged-memory witnesses |
| `__heap_share(p)` | Data only, checked increment, preserve input on overflow | Counted-model laws and retain instruction kernel; surviving alias, Type-share rejection, RC ceiling memory preservation |
| `__heap_open(p)` | Unique transfer/free; shared child acquires then parent decrement | Unique-open instruction kernel; repeated-edge RC balance and overflow laws; actual repeated-child success and full-memory rollback witnesses |
| `__heap_enqueue(p)` | Transfer root into bounded pending work | Frame-bound instruction kernel; zero-capacity rejection preserves owner and every memory byte |
| `__heap_clean(budget)` | Bounded progress; retained cursor on budget/stack limit; free after children | First/final-release and zero-budget model laws; pending/drop/free instruction kernels; budgets 0/1/sufficient, 65-cell limit-1 resume, 3277-cell chain |
| `__heap_release(p)` | Enqueue and drain; duplicate release is internal failure | Alias survival/final release witnesses; duplicate release preserves memory and live count |
| Memory/counters/limits | Accurate physical/debug observation | Fixed-page/no-growth checks; allocator next/free heads/every cell state/count-or-next/class/owner serial against independent Bend model |

`__heap_live` and `__heap_peak` count cells, including state-2 dropping cells.
`__heap_allocations` counts successful allocations, including reuse; it rejects
at 2147483647 rather than wrapping. `__heap_bump` is the allocator high-water
byte address. `__heap_pending` and `__heap_peak_pending` count release frames.
`__heap_status` is 0 success, 3 Exhausted, or 5 InternalFailure. Source Invalid
and Unsupported remain checker/compiler outcomes. Host launch/IO failures are
separate gate outcomes. `clean` and `enqueue` return their bounded status;
compiler-facing alloc/share/open/release trap after setting the status. Debug
`__heap_stack_limit` and `__heap_rc_limit` return the previous bound.

## Proof boundary

The heap packet contains **30 filled equations in two complete proof entries**:
`src/heap-PROOF.bend` checks 17 layout/emission equations in `src/heap-LAWS.bend`;
[model-PROOF.bend](model-PROOF.bend) checks the 13 independent semantic equations
in [model-LAWS.bend](model-LAWS.bend). Both entries print `All terms check.`
Keeping model laws under this test directory leaves the compiler's source import
closure independent of the test and research models. No law or assertion was
weakened or removed. Together with the 13 ownership equations, the increment
retains 43 filled laws. No hole, new axiom, unsafe primitive, or foreign heap
implementation is introduced.

- **Seven semantic allocator equations** use independent
  [model.bend](model.bend): successful allocation/round-trip, exact-class reuse,
  wrong-class/full rejection, unrelated-owner preservation, and duplicate release.
  They normalize inhabited one/two-cell pools with arbitrary scalar owner serials.
- **Six semantic RC equations** use the packet's independent-to-emitter
  `research/data-lifetime/model.bend`: allocation starts at one, a surviving
  alias after first release, last-release reclamation, both duplicate child
  acquires, transactional duplicate-child count overflow, and zero-budget
  pending preservation. They are fixed-shape graph equations with arbitrary
  scalar tags, not arbitrary-graph theorems.
- **Seventeen layout/emission equations** constrain actual compiler helpers:
  seven address/size normalizations, nine emitted ownership/descriptor kernels,
  and arbitrary zero-encoding-fuel failure. The kernel equations establish exact
  instruction structure. They do **not** prove execution semantics by themselves.

There is no universal proof that generated Wasm refines either model, no
inductive whole-heap RC invariant, and no general source-to-Wasm correctness
proof. Runtime-model agreement and source differential tests supply finite
refinement evidence separately. In particular, a model proven correct alone is
not counted as runtime acceptance.

The allocator oracle is a persistent list model with explicit free/live cells;
it imports no allocator, instruction builder, byte encoder, or emitted output.
Its 12 observations include all represented allocator metadata and owner serials,
not an opaque checksum. The runtime probe additionally has **10 actual Wasm
witnesses** covering count/open/release/bounds composition. Source-level fixtures
and the five required semantic mutants are recorded by `check.py` separately.
No parser/type failure is a semantic mutant kill.

## Hostile reread and limits

The retained controls distinguish always-leak, premature-free, missing-retain,
wrong-size reuse, double-release, duplicate-child undercount, and a wrong release
stack bound. Shared-open overflow freezes a copy of the complete memory before
the call; it compares that copy after failure and then exercises successful
cleanup. Reusing an aliased memory view would not establish preservation.

All memory access/debug calls are privileged. Forged pointers, backpatched
cycles, copied instances/snapshots, or externally duplicated Type owner bits are
outside the construction contract. Internal pointer guards are defensive; they
are not a hostile-memory decoder or a generation/arena capability system. This
increment establishes source-local ownership and reuse, not the R4 global arena,
restore, stale external locator, or GPU reader protocol.

A successful source call returns exactly its reachable owned graph. A failed
**whole source invocation is not a transaction**: prior source allocations may
remain live and Wasm unwinding can abandon local/staged roots. Retire that
instance after a source trap. The explicitly exported `enqueue/clean` path is
resumable with its queued root; this is narrower than recovering an arbitrary
trapped source call. In particular, artificially limiting cleanup inside a
source call can retain the current cleanup graph while losing unrelated Wasm
locals. The independent review records that boundary in `REVIEW.md`.

The profile is sequential and immutable. GPU reader barriers, disposer closures,
cyclic/mutable graphs, arbitrary external roots, variable-width fields, heap
growth, compaction, and proof of general allocator refinement remain open.
Shared-open preflight scans slot multiplicity and is quadratic in the number of
live slots; no constant-time-open claim is made. Reclamation is linear in visited
slots/edges plus descriptor dispatch, and compiler function recursion remains a
separate backend concern.

Before the semantic-law files were separated from the source import closure,
offline preflight was run on the four new heap source files and the three Bend
component-probe/model files with this directory's `SPEC.md`: 155 declarations,
seven files, zero provider requests. It reports 12 truncated declaration
contexts and 24 declarations without complete supporting-role context.
Composition is unavailable (54,638/48,000 bytes and 60 nonlocal-import gaps).
No live Compression, Delight, memetic identity, Anticipation, or Payoff ratings
exist for this sidecar; this is not an automatic style pass. The coordinator
owns live review and the integrated group's final preflight after the law-file
split; the counts above are the earlier snapshot, not the final file selection.
