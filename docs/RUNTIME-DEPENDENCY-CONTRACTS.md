# Remaining runtime dependency contracts

2026-09-26. Handoff following seed CPU checkpoint `b61df8d` and bounded Wasm
word-store checkpoint `7478516`. These are remaining integration contracts and
acceptance probes, **not newly implemented components or proof results**.
Compiler Planning owns flat-store implementation/documentation and subsequent
compiler/runtime integration. This document supplies its dependencies; it changes
no published package and selects no Data reclamation strategy. The
[support plan](RUNTIME-SUPPORT-PLAN.md) records qualified evidence.

The [flat store](../research/flat-store/SPEC.md) executes scalar-word transitions
in actual Wasm, with fixed cell addressing and a three-U32 list codec. It does not
yet qualify mixed-width compact field descriptors, a twelve-byte adjacent-locator
transport, global arena/restore authority, shared Data roots or device lifetime.
The frontend still emits only the enum profile; all six longer-goal milestones
remain open.

## Arena identity and serialized ownership

The current [Store contract](../research/owned-store/SPEC.md) accepts a caller's
arena ID. Generation retirement prevents same-store reuse of a live identity;
it cannot distinguish two stores given the same arena ID. A reusable three-word
locator also cannot carry the authority to instantiate or restore an owning store.

Define the comparison universe explicitly: every running store, retained locator,
host snapshot, suspended task, device buffer and serialized image whose locators
can later meet belongs to that universe. Arena IDs must never be reissued there.
A process restart or empty live-store table does not establish an empty universe.

The smallest issuer model is an affine authority with `Next(n)` or `Spent` state,
and an inclusive U32 ceiling. `issue` returns one arena reservation and the next
authority. Issuing the ceiling enters `Spent` without adding one. Failed issue
preserves the authority. Destroying an arena never returns its ID to a free list.
An issued reservation may be burned on failed construction; it is never recycled.
The issuer is separate from object allocation and from any task-attempt identity.

This is a finite-domain contract: exhaustion is a result, not permission to wrap,
randomly guess another ID, or silently reset. Runtime adapters must serialize
issuance or obtain disjoint reservations from one authority. If locators can
survive a process, the authority must also survive without rollback, independently
of restorable heap snapshots. An old saved high-water mark is not that authority.
Until this boundary exists, keep cross-process restore unsupported. Independent
universes may use overlapping numbers only if the host/import boundary prevents
their locators from meeting; the three words alone cannot enforce that boundary.

Serialization needs two distinct guarantees:

1. **Fresh identity:** importing into a newly issued arena remaps every permitted
   internal reference and exported root to the new identity. Escaped old locators
   cannot access the new arena. Preserve slot generations and retired states;
   never repair an invalid reference by substituting a cell's current generation.
2. **Single ownership:** copying snapshot bytes must not instantiate a second
   owner of an affine payload. Fresh arena IDs alone do not provide this. Moving
   a Type graph requires a single-use transfer authority that is not duplicated
   with the bytes, and exclusion of the old execution authority. Unsupported
   affine resources need an explicit rejection, not a byte-copy approximation.

For a first move/restore contract, `seal` consumes the store and its execution
authority after writers/readers quiesce; it returns an immutable image plus a
transfer ticket. A failed seal returns the original owners. `restore` validates
the image, obtains a fresh arena reservation, relocates the closed graph and
publishes the new owners once. The ticket is consumed only by successful
publication; failure returns a retryable ticket and cleans or retains all staging
owners explicitly. A reserved ID may remain burned. Across processes, single-use
tickets require an authority outside copyable/rollbackable snapshot data.

Preserving the old arena ID is a separate, stronger resume mode. It requires an
exclusive transfer of execution authority, the exact sealed state, no transitions
after sealing, and rejection of old, replayed or superseded images. A hash proves
neither recency nor exclusivity. Do not enable this mode using a snapshot's own
generation counters or stored issuer state. Data-only cloning may be a separate
operation when the graph has no affine owners and external references have an
explicit lifetime contract.

The image must identify its schema/layout version, comparison universe, arena
state, logical capacity, generation ceiling, cells, free-list order, typed edges
and exported roots. Validate all bounds/tags/generations before publication; the
free list contains each vacant slot once and no live, retired or padding slot.
Unknown external edges, outstanding device readers and unsupported task captures
are explicit unsupported cases until their transfer protocols exist. Validating
an image must not execute destructors or mint live owners from partial input.

Smallest acceptance probes, all pending:

| Probe | Independent observation | Mutant to reject |
| --- | --- | --- |
| Two arena lifetimes, same slot/generation | Issue arena 0 with payload 7; retain its locator; dispose the store; issue arena 1 with payload 9. The old locator fails WrongArena and 9 remains present. | Recycle a destroyed arena ID. |
| Issuer ceiling | Use ceiling 1: issue 0 and 1, then return exhaustion without changing any live store. Also normalize the actual U32 ceiling transition without allocating billions of stores. | Wrap, reset on empty registry, or overwrite a live reservation. |
| Move and replay | Seal one owning payload, restore once into a fresh arena, then attempt both a second restore of copied bytes and continued old execution. Exactly one owning store exists. | Treat the image, or a copied ticket field inside it, as fresh authority. |
| Rollback and relocation | After sealing, introduce a newer issued ID; an older image cannot roll the issuer back. A two-object internal edge and exported root both relocate; an escaped old locator remains invalid. | Restore the snapshot high-water mark, remap roots only, or refresh a stale edge's generation. |
| Restore failure | A truncated image or staging-capacity failure preserves the transfer ticket and all obligations; a retry succeeds once. | Leak a partial owner, consume the ticket on failed validation, or publish partial state. |

## Compact fields and the locator transport

The existing Wasm layout has an eight-word header and four-word scalar cells at
byte `32 + 16*i`, bounded by capacity 4096. Its `[arena,slot,generation]` utility
is a Bend word-list codec. Neither that round-trip nor the actual Wasm scalar
loads/stores discharges the independent twelve-byte/adjacent-locator contract
below. Fixed-stride cell arithmetic is evidence for that profile, not general
mixed-width descriptor arithmetic.

Keep the existing source declaration order, lexical identities and match frontier
separate from the runtime layout. Erased declarations retain checking metadata
but have no value words. Each live field has a compact slot plus a representation
descriptor: width in words, alignment, word offset, declared type/kind/quantity,
and edge role (scalar, owned child or reusable Data reference). A quantity-1 Data
binding still has affine source-use restrictions; kind and quantity do not collapse
into one ownership bit. Header/tag placement belongs to a versioned target profile.

The proposed transport uses a flat storage array of U32 words. A locator occupies
exactly three consecutive words in order `(arena,slot,generation)`, each encoded
as four little-endian bytes. These are a locator's representation, not permission
to extract a payload. Do not reserve an all-zero locator as null unless the profile
also excludes that otherwise valid identity; represent optionality explicitly.

WGSL gives `u32` a four-byte size/alignment and uses little-endian numeric buffer
layout. Its `vec3<u32>` size is twelve bytes but alignment is sixteen, so an array
of those vectors has sixteen-byte stride. The flat-word design therefore requires
explicit indexing rather than assuming a vector array is packed. This is an ABI
proposal derived from the [WGSL alignment/stride rules](https://www.w3.org/TR/2026/CRD-WGSL-20260921/#alignment-and-size)
and [numeric buffer layout](https://www.w3.org/TR/2026/CRD-WGSL-20260921/#internal-layout-of-values),
not evidence of device execution.

Example: erased/scalar/erased/locator declarations have compact slots
`[none,0,none,1]`, live widths `[1,3]`, and payload word offsets `[0,1]` in the
initial four-byte-aligned profile. Their payload occupies four words, not two.
An independently fixed payload `[7,41,0,3]` must decode to scalar 7 and locator
`(41,0,3)`. Add checked header offsets separately; never use a lexical level or
compact slot number directly as a byte offset. Recursive fields use indirection
unless a separately checked finite inline layout exists.

Validate the whole descriptor: compact slots are contiguous, live spans are
aligned and nonoverlapping, no field overlaps the header, and every span fits
within the record stride. Edge roles agree with the checked type/quantity metadata;
a forged layout ID must not turn an owned Type edge into a reusable Data edge.

Use unsigned, unit-specific arithmetic and check **before** computing a machine
result. With representable ceiling `M = 4294967295`:

- Addition `x+y` requires `x <= M` and `y <= M-x`.
- Multiplication `x*y` branches on `y=0`; otherwise require `x <= floor(M/y)`.
- Alignment requires a valid nonzero power-of-two `a`. Compute
  `pad = (a - (x mod a)) mod a`, then use checked addition for `x+pad`.
- A word span `(offset,width)` in `N` accessible words requires `offset <= N`
  and `width <= N-offset`. A dereference additionally needs positive width.
- For a record table at word base `b`, capacity `c`, positive stride `s`, require
  `b <= N` and `c <= floor((N-b)/s)` before allocating/decoding. An access requires
  `slot < c`; only then compute `b + slot*s`. Physical padding does not raise `c`.

The initial transport exposes at most `floor(M/4)` words, so its exclusive byte
length is representable too. Check word-to-byte multiplication by four, then
check any enclosing memory-base addition against the accessible byte region.
This is an explicit bounded profile, not support for every possible Wasm memory
size. The actual Wasm region and effective GPU binding size may impose smaller
limits. Never replace these checks with masking, wrapping arithmetic or a backend's
out-of-bounds behavior. Empty tables may exist without allowing an element read.

Decoding a locator only yields three numbers. Before access, validate the owning
store/arena context, logical slot bounds, cell state and generation; retain the
seed store's WrongArena-before-Bounds behavior and its distinct Stale/Vacant/Retired
results. Validate the record's declared layout/tag before traversing fields. Bad
encodings/layouts are malformed runtime input; capacity exhaustion is a resource
result. Neither establishes that a source program is semantically invalid.

Smallest remaining transport/heterogeneous-layout probes, extending the already
qualified fixed-cell and word-codec cases:

- Encode `(0x01020304,0x11121314,0x21222324)` as the fixed twelve bytes
  `04 03 02 01 14 13 12 11 24 23 22 21`. Test two adjacent locators to distinguish
  twelve-byte from sixteen-byte stride. Codec round-trip alone is insufficient:
  one shared wrong encoder/decoder can pass it.
- Construct/unpack the mixed-width example above with shadowed pattern binders;
  erased fields neither run nor advance the value cursor. Independently decode
  the emitted bytes and compare ordered values and edge roles, not only length.
- Exercise zero/one capacity, physical padding, truncated headers/locators, bad
  tags, foreign arenas, exact-fit and one-word-short buffers. Arithmetic-only
  tests cover M, multiplication overflow and alignment rounding without allocating
  a four-gigabyte fixture. Actual small buffers carry canaries on both sides.
- Kill type-correct mutations for reversed endian/word order, vec3 stride,
  erased-slot advancement, byte/word confusion, wrapped offsets and padding access.
  The same fixed observations must hold for generated Wasm and actual WGSL storage
  transitions. A host-only serializer or successful shader compilation is not that
  gate. Keep generated-source GPU lowering separate from handwritten qualification.

## Reusable Data and suspended roots

Use an abstract ownership graph before choosing arenas, reference counting,
tracing or copies. An owned Type edge has one current owning path. A reusable Data
edge permits multiple live holders with immutable value agreement. Erased fields
have neither kind of runtime edge. Copying a locator registers neither an owner
nor a lifetime root; dereference must be justified by a live holder/read lease.

The root model must cover all of these states:

| Holder | What keeps its values alive | Release/transfer point |
| --- | --- | --- |
| Caller or live object | Owned children and Data edges in its live descriptor | Successful move, logical drop or holder release |
| Ready/running/suspended task | Live captures and saved continuation fields | Transfer into the next state, result publication or cancellation |
| Partially filled join | Each delivered result in its logical slot; retained parent continuation | Successful ordered join or explicit cancellation cleanup |
| Submitted GPU reader/retained snapshot | Readable backing storage until the declared completion barrier | Completion acknowledgement, not dispatch submission |
| Cleanup or restore in progress | Pending worklist, transfer ticket and staging owners | Completed cleanup/publication or retained retryable state |

Every transition must preserve the ownership graph on rejection or state exactly
where each obligation moved. Moving a capture does not copy its Type children.
A parent reconstruction recipe is not another owning root; a retained backing
container may still need a separate lifetime pin. Partially completed joins cannot
release a Data value merely because the sibling has not yet arrived. Duplicate or
late completion returns or explicitly disposes its incoming owner under the task's
attempt protocol; object generation alone does not establish attempt freshness.

Physical reuse is allowed only after no permitted holder, in-flight reader or
pending cleanup can access that storage. Logical drop and byte reuse remain
distinct. Budget exhaustion retains the worklist and every value it protects.
A failed `release` in the current seed store does not call its disposer, but its
API also does not return that affine closure: captures of a discarded disposer
need a lifetime/drop contract. The existing disposal-serial observations establish
neither that cleanup nor general payload destruction.

The smallest R3/R5/R7 witness graph has an owned child with serial 7 and a Data
value with distinguishable contents 9 and 11. Keep one Data holder in a suspended
frame and another in the delivered left slot of a waiting join. Move the Type
child into that frame as its sole owner. Release the
original caller, attempt reclamation, resume the frame and read both Data fields;
then deliver the right result and check ordered joining. Separately cancel each
state, submit a duplicate/late result, and exhaust cleanup fuel at zero/one.
Track every child and rejected owner, all surviving values and pending readers.

After the last holder and reader finish, supply sufficient cleanup budget and the
candidate policy's release boundary. The finite witness must reach reusable storage
or a documented bounded-retention state that becomes releasable at that boundary.
An always-retain implementation cannot satisfy this progress obligation. Kill
mutants that omit the suspended/partial-join root, free after one of two Data
holders releases, double-drop a child, discard an unused disposer capture, reuse
before reader completion or lose a cleanup work item.

Copies, regions, RC and tracing may realize this abstract contract differently.
Require each candidate's explicit alias/cycle policy, capacity-failure behavior,
reader barriers and retention bound; compare values and ownership observations
without requiring identical allocation counts. Record copied words, traversed
edges, retained bytes and cleanup work separately. No policy is selected here.

## Ownership and next increment

Compiler Planning has qualified the word transitions in checked flat Wasm with
distinct supplied arena IDs as a bounded precondition. Next extend the fixed
layout to mixed-width field descriptors/edge roles and independently qualify
twelve-byte locator transport; actual GPU storage remains pending. Preserve the
independent Bend model, literal observations, error precedence, failed-owner
preservation and generation-ceiling controls. Do not replace semantic mutation
checks with compile failures or weaken the CPU/Wasm gates.

In the current Wasm ABI, failed ordinary operations may update result registers
while preserving logical store fields. Pre-init, capacity-rejected init and
repeated init preserve all bytes. Before-images used to establish preservation
must be frozen copies, not aliases of the mutable memory. The retained valid-module
write-on-reinit mutant distinguishes a correct error status from unchanged state;
the historical aliased-buffer receipt cannot establish that observation.

The issuer/restore and Data-root contracts above remain pending dependencies.
Published Vec/IntMap/TermStore can hold reusable descriptors, relocation maps and
model metadata; they do not supply unique ownership, persistent ticket authority
or physical root tracking. OutputBuilder can emit reviewed bytes but is not the
store or its address validator. No additional package chat or publication is
assigned. This documentation change has no changed executable declaration or
law packet requiring a new Perch/style request.
