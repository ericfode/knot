# Runtime support for structural Bend and reproducible Wasm

2026-09-26. Coordinator handoff to Compiler Planning. The approved longer goal
is full Bend self-hosting through reproducible Wasm A2/A3, followed by
compiler-generated WebGPU adaptive continuation tasks. The
[active goal](SELF-HOSTING-GOAL.md) requires GPU storage, continuation, join and
reclamation qualification alongside structural runtime work, before bootstrap
completion. Final generated-device acceptance follows A2/A3. The
[bootstrap protocol](BEND-SUBSET-STAGES.md#bootstrap-protocol-and-first-self-compiling-stage)
defines A2/A3 and the independent conformance obligations. This plan supplies
early runtime contracts and stage-specific evidence; it does not establish a
complete owning heap or generated device runtime. The six-package campaign
remains paused.

Compiler Planning owns `src/`, structural fixtures and compiler/runtime
integration. Existing package owners retain their published sources. No new
package assignment, publication or memory-management strategy is selected here.

## Qualification status: seed CPU and bounded Wasm

Commit `b61df8d` adds [research/owned-store](../research/owned-store/README.md),
owned by Compiler Planning. Its affine `Store<A:Type>` qualifies R2 ownership
transitions and part of R4 on the seed's native and Bun backends. Reusable
locators contain arena/slot/generation; extraction still consumes the Store.
Failed put/full preserve both store and incoming payload. Take increments below
the ceiling and permanently retires at the ceiling without wrapping.

The [stored gate](../research/owned-store/receipts/gate.json) contains fourteen
filled equations, 3,532 independent-model traces per backend, fifteen literal
witnesses, six type-correct semantic mutant kills, five quantity controls and
four max-1/max generation observations. The equations include generic cell and
disposer laws plus singleton/concrete normalizations; they do not prove arbitrary
Array/list refinement or general composition. The [handoff audit](runtime-support-owned-store-2026-09-26.json)
rechecked source/artifact hashes and stored observations, including 84 referenced
trust files. It reran no compiler, device or model-review command. Recorded Perch
coverage is 188 checks; all-three-axis style acceptance remains unmet.

Source inspection shows balanced-array access and a free-list scan for explicit
put; alloc/take operate on the free-list head in addition to array access.
Completion through capacity 4096 is not an empirical complexity bound, a speedup
or evidence of constant-time destruction.

Commit `7478516` adds [research/flat-store](../research/flat-store/README.md):
a Bend-written instruction/module emitter produces a fixed **1,050-byte Wasm
word store**. Native and Bun emit identical bytes with SHA-256
`0dfc76faa3a89c6d78f9a30e0a2c8e60de54158bf5181246e9a4106d36f4dbc4`.
Node executes that module; this is bounded R2/partial-R4 runtime qualification,
not a change to the Knot frontend's enum-only emission profile.

The [flat-store gate](../research/flat-store/receipts/gate.json) records 3,534
instances and 13,621 status/full-logical-word observations per emitter lane,
seven lifecycle checks, 24 literal word-codec/address/instruction probes and
nine valid-module semantic mutant kills. Fifteen filled equations comprise five
quantified codec/failure equations and ten concrete normalizations, with zero
holes; there is no universal Wasm transition-refinement theorem. The
[flat-store handoff audit](runtime-support-flat-store-2026-09-26.json) matches
17 Bend sources and 92 referenced trust files, checks oracle/report identities,
and independently validates the binary and its exports. It does not replay
transitions: successful execution reports retain assertion summaries rather than
every actual memory image. The recorded all-three-axis style bar remains unmet.

Payloads are scalar words representing owners. The actual store has an eight-word
header, four-word cells, capacity at most 4096 and a fixed two-page memory.
Backing memory exists at instantiation; rejected capacity avoids logical
initialization, not that backing reservation. Ordinary failed operations may
change result registers while preserving logical store state. Pre-init operations
and rejected initialization preserve every byte. The repaired reinit check freezes its
before-image; a valid-module mutant returning the correct error but writing memory
fails it. The earlier aliased-snapshot receipt is historical, not preservation
evidence. General Type graphs, Data lifetime, global arena authority and GPU
storage remain outside this qualification. All six goal milestones remain open.

| Gate | Current evidence | Still required |
| --- | --- | --- |
| R1: layouts | Structural declaration/live-field semantics; fixed four-word cell addressing and a three-word locator utility. | Mixed-width compact field descriptors with edge roles, heterogeneous address arithmetic, and independent twelve-byte/adjacent-locator transport qualification. |
| R2: owning storage | Generic Type ownership under the seed; actual Wasm word-payload transitions, preserved rejection and retirement against the Bend model. | General transition refinement, nested-object representation/ownership, actual GPU storage and compiler field lowering. |
| R3: reusable Data | [r3r7 policy models](../research/data-lifetime/README.md): copied Data and unique Type plus RC Data agree with independent graph observations, including surviving aliases and suspended/partial-join holders. | Policy adoption, actual owning payload/emitter refinement and device lifetime qualification. |
| R4: freshness | Same-store generation rejection/retirement in seed CPU and bounded Wasm, max boundaries and three-U32 list round-trip. | Non-reused arena issuance, serialized ownership/restore and twelve-byte transport. Arena uniqueness is still a caller precondition; the word codec yields numbers, not extraction authority. |
| R5–R7: tasks and reclamation | Earlier bounded adaptive-task/Slot probes remain separate evidence. r3r7 adds model traces for frames/partial joins, cancellation, bounded cleanup and a global reader-completion barrier. | Generic owned captures, joins/frontiers, bounded worklist allocation and actual reader-safe device reclamation for this object store. |

The [remaining dependency contracts](RUNTIME-DEPENDENCY-CONTRACTS.md) specify
arena issuance and single-owner restore, the proposed three-word transport with
checked layout arithmetic, and Data roots across suspension, partial joins and
device readers. Their remaining probes are pending. Compiler Planning owns the
flat-store implementation/documentation and subsequent compiler/runtime
integration. The coordinator owns this dependency plan. No package release is
changed and no ownership boundary is transferred by this handoff.

## Reference constraints and layout model

A bounded pinned-reference pass of thirteen structural fixtures at the initial
handoff produced the expected seven successes and six rejections. The
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

## Structural matching and ownership

The [structural-term contract](../research/compiler-fields/SPEC.md) supplies a
further constraint on R1–R3. The original
[field-contract review](runtime-support-fields-2026-09-26.json) records source
inspection of then-uncommitted work, without rerunning compiler/runtime gates.
The subsequent [structural milestone](../research/compiler-fields/README.md)
records the owner's checker/evaluator evidence; it still establishes no owning
heap or Wasm field lowering.

Opening an affine constructor transfers its live fields into the branch. A use
of the matched parent is a **reconstruction from those fields**, not another
owner of the unopened object. In [patterns.bend](../src/patterns.bend), `finish`
records that reconstruction; [check.bend](../src/check.bend)'s `Rebuild` resolves
its references through stable lexical identities and rechecks their current
quantities/refinements. Shadowing changes name lookup, not those identities.
A later field match must refine parent reconstructions that refer to that field.

Consequently, consuming an unrefined affine field and reconstructing its parent
cannot consume the same field twice. Do not replace this rule with a blanket
ban on using a parent after any field match: a nullary constructor refinement
can supply a fresh value, removing the original field-use dependency. Reusable
Data fields may support repeated reconstruction where their effective quantities
permit it; this grants no duplicate owner of a `Type` child. Reconstruction may
reuse storage or allocate anew, but must preserve these transfers, values and
exhaustion behavior. No physical object-identity promise follows from the parent
name or its reconstruction recipe.

Keep four maps separate: declaration position, stable lexical identity, ordered
match eligibility and compact live-slot position. In [scope.bend](../src/scope.bend)
and `patterns.finish`, matching identity `p` changes the match frontier to
`field_ids ++ suffix_after(p, frontier)`. Newly introduced fields precede later
parameters even though their lexical levels are allocated later. Removing the
earlier prefix removes match eligibility; it does **not** itself perform a runtime
drop or remove ordinary variable lookup. Local lets close match eligibility;
runtime ownership/liveness remains a separate obligation.

A minimal checker control starts with parameter identities `[0,1]`, matches 0
and introduces field 2: the next frontier is `[2,1]`. Matching 2 then 1 is
permitted; matching 1 then 2 must fail for match eligibility, not parsing. Existing
[forward-order](../tests/compiler-fields/fixtures/field-before-parameter.bend),
[reverse-order](../tests/compiler-fields/fixtures/parameter-before-field.bend),
[shadowing](../tests/compiler-fields/fixtures/duplicate-pattern-names.bend) and
[parent-refinement](../tests/compiler-fields/fixtures/field-then-parent-refinement.bend)
fixtures give concrete controls; their current code was inspected, not rerun here.

The independent [evaluator](../src/eval.bend) keeps declaration metadata in
`Construct`/`Fields`, skips erased arguments before evaluation, and stores only
live values in declaration order. `Unpack` skips erased binders without advancing
the live-value cursor. R1 must use the same projection for construction and
unpacking, while retaining erased declarations for checking and lexical identity.
The evaluator's reusable tree-shaped `Value` and retained environments model
checked results; they do not implement affine heap extraction or reclamation.
The emitter still rejects fielded books through `enum_profile`.

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
| [Owning store qualification](../research/owned-store/SPEC.md), not a published package | Bounded indexed Type owners, ordered free IDs, preserved failed insertion, take/release and generation retirement under the seed. | Supplied arena IDs, trusted internal constructors and synchronous operations; no packed target storage, shared Data lifetime or general heap refinement. |
| [Flat Wasm store qualification](../research/flat-store/SPEC.md), not a published package | Actual init/put/alloc/take/release for bounded scalar words, with an independent Bend model and whole-logical-state/canary checks. | Word proxies do not establish generic Type ownership in Wasm. Exported memory/host calls are privileged; no mixed fields, byte-locator transport, restore, shared Data or GPU store. |
| [Affine Slot probe](../research/adaptive-tasks/slot.bend) and [task/device protocol](../research/adaptive-tasks/DEVICE-PROTOCOL.md) | Seed contracts for put/take, suspension, logical destinations and phase-separated execution. | Slot is singular; device records are tree-shaped and never reused. They do not extend the new CPU store to shared Data, generic captures or safe reclamation. |

Wrapping an address in a `Data` record and putting it in Vec or TermStore does
not close these gaps. The object state and authority to transfer/drop its contents
must be specified and validated separately.

## Missing contracts and smallest acceptance probes

The table defines end-to-end acceptance requirements. R2 and part of R4 have the
seed CPU and bounded Wasm word-store evidence above; general heap, field integration
and GPU refinements remain open. Remaining runtime probes are **proposed**, not
completed tests. Keep the independent state/ownership model in Bend and carry its
observations into generated Wasm. Qualify device layouts/lifetimes with focused device probes
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

Structural matching adds three focused requirements to these proposed probes:

- **R1:** Construct and unpack erased/live/erased/live fields with distinct live
  values and shadowed pattern binders. Check declaration-to-slot and lexical-to-slot
  maps independently. Kill mutants that advance the live cursor for an erased
  binder, use lexical levels as offsets, or substitute by spelling rather than
  identity. Include the `[2,1]` match-frontier control above.
- **R2/R3:** Open a `Type` object containing an owned nontrivial child and reusable
  Data, reconstruct it, then extract/drop each owned child once. A competing use
  of an unrefined affine field and its parent must fail the checker; a matched
  nullary-field reconstruction is the valid neighbor. Preserve a permitted Data
  alias across reconstruction and release. Kill an implementation that retains
  both the old parent owner and the extracted fields, and one that loses the
  surviving Data lifetime obligation.
- **R5/R7:** Suspend immediately after opening and after reconstruction, then
  resume or cancel each case. A reconstruction recipe in compiler metadata is
  not an additional runtime owning root. Keep each required field alive without
  capturing/dropping both a parent owner and those same extracted owners. If a
  representation keeps a container as backing storage, account for that lifetime
  separately and demonstrate a single owning path to each affine child.

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
| Copied Data | Every physical record has one owning path; consumption frees the parent and transfers fields. | Reuse creates a deep independent copy; releasing one copy cannot affect another. | Reserve the complete copy or retain/roll back unpublished staging; measure expanded trees, failed-copy work and reader-safe cleanup. |
| Regions/epochs or bounded arenas | Moves/extractions still invalidate prior owners; logical drop releases owned edges even if bytes are retained. | Every alias must remain within a live region, or an explicit escape/promotion mechanism extends its lifetime. | A region cannot end while a suspended frame, join or GPU reader retains it. Measure retained memory and explicit exhaustion; never silently abandon owners to reset an arena. |
| Unique Type objects plus reference-counted Data | Type payloads have one owning transfer path; dropping a Type object visits its owned children and releases its Data edges. | Every retained/shared Data reference has balanced acquire/release, checked count bounds and a defined last-release action. | Prove runtime cycles excluded or provide cycle handling; recursive datatype declarations alone settle neither. Establish GPU synchronization/publication and bounded resumable release cascades. |
| Tracing collection | Tracing does not enforce affine ownership; the checker/runtime must still prohibit duplicate extraction and account for logical drops. | Trace every live Data alias through accurate field descriptors and all task/host roots. | Establish safe points across device readers and suspended continuations. Moving storage needs stable indirection or complete relocation; handle freshness survives reuse. |

Data may instead be copied where the language permits. That choice must account
for copy cost, capacity failure and ownership of the resulting independent values;
it cannot be assumed cheap for recursive structures. A hybrid must specify which
representation each type/layout uses and how edges cross the boundary. Run R2,
R3 and R7 on the candidate before adopting it. No choice is made in this plan.

### r3r7 decision packet (2026-09-27)

[research/data-lifetime](../research/data-lifetime/README.md) evaluates copied
Data (A) and unique Type plus reference-counted immutable Data (B), without
editing `src/`. Frozen host/literal expectations precede the Bend implementation.
Both policies have alloc, take, share and release models, 20 filled laws checked
through the complete proof entry, an independent host graph oracle, 105 common
traces per candidate, 6,788 complete-state observations across seed native/Bun,
20 literal checks, 1,691 cross-policy value/holder comparisons and 16 type-correct
semantic mutant kills. The [gate](../research/data-lifetime/receipts/gate.json)
retains hashes, actual state transcripts, exact counters and failure witnesses.

The packet **recommends B for coordinator/user decision**. Eight successive
shared-subterm constructions use 43 logical peak words and 9 allocations under
B versus 1,532 words and 511 allocations under A. A unique wrapper rebuilt 64
times instead uses 5 peak words under A and 6 under B, exposing RC metadata cost.
These are committed policy/space counters, not process memory, timing or GPU
measurements. `bench/` currently accepts enum source/nullary Wasm workloads; it
needs a stateful trace/counter interface before this experiment can use its timers.

Keep the `knot-fields-wasm-1` `[tag][live slots]` payload contract. B needs RC
metadata outside those slots, checked retain/release helpers, explicit move/share/
drop decisions, a unique/shared opening path, descriptor-driven last release,
a resumable cleanup worklist and a reclaiming allocator. Both candidates require
failure-owner preservation and reader completion before physical reuse. The
campaign's bump arena remains **interim and non-closing** for owned storage.

D5's GPU record interpreter can represent these same holder/edge obligations.
The packet maps A to explicit copy frames and B to a proposed dispatch-separated
RC-delta path with one owning writer per object. Neither is qualified device
code. Do not use unique-parent task retirement to reclaim a shared Data DAG, or
count a reserved frontier position as publication. Actual transport, stale task
attempts, capture cleanup, bounded worklist allocation and GPU synchronization
remain separate gates.

The Bend store contains ownership metadata, not generic affine payloads; its
Type wrapper does not make copyable metadata into extraction authority. Four
source fixtures agree with the seed interpreter and independent Knot evaluator;
this checkout reports fielded Wasm **Unsupported**. The packet therefore supplies
a decision and integration gate, not general heap refinement or milestone closure.
All 11 existing gates were freshly rerun unchanged. Offline Perch preflight has
15 truncated declaration contexts; live review remains with the coordinator.
No policy is adopted by this evidence. Next integrate the selected policy and
replay the same observations in actual Knot Wasm and on GPU before accepting it.

## Increment order, law quality and efficiency

1. Carry declaration/type/quantity metadata and R1's live-slot projection from the
   existing compiler into checked packed records. Specify versioned target layouts
   separately from source declaration order. Keep recursive kinds/name resolution
   independent from heap strategy.
2. Extend the qualified CPU/flat-Wasm word-store observations to checked mixed-width
   fields and the separate twelve-byte locator transport, then compile one
   constructor, deconstruction and drop path. Qualify GPU storage alongside this
   work. Preserve failure ownership and generation/error behavior. Distinct supplied
   arena IDs may remain an explicit bounded premise; they do not close issuer/restore
   qualification. Select a Data lifetime policy only after the decision gate.
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
does not establish useful storage. Seed CPU and flat Wasm evidence close only the
bounded obligations listed above. New issuer/restore, mixed-field/byte-transport
and Data-root/device probes remain unrun; this documentation audit does not execute
store transitions.

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

The initial increment added this plan and the thirteen-case reference receipt
and linked them from the campaign notes. The structural-matching follow-up adds
the source-review record and the implications above. Its working-copy sources
remain owned by Compiler Planning; hashes identify the inspected versions, not a
validated compiler build. These documentation increments change no package,
compiler or probe source.

The owning-store follow-up audits stored evidence at `b61df8d` and adds concrete
remaining dependency contracts. The flat-store follow-up records `7478516` and
audits its bounded Wasm qualification without treating words as a general owning
heap. Mixed fields, byte transport, GPU storage, arena restore and general
lifetime/reclamation gates remain open.
For those documentation-only audits, Perch was not applicable: no owned executable
declaration or law packet changed, and no semantic-pass claim was made. The later
r3r7 decision packet above adds model execution and offline preflight separately.
Policy adoption, general compiled allocation and generated GPU lifetime validation
remain future work.


## GPU runtime campaign checkpoint (2026-09-27)

The bounded [record interpreter](../research/adaptive-tasks/runtime/README.md)
adds implementations and independent Bend controls for **R4** and **R6** under
[`knot-device-records-1`](WASM-WEBGPU-BACKEND.md#device-record-contract-knot-device-records-1).
The original tree probe, published packages and compiler sources are unchanged.

| Obligation | Added controls | Current evidence |
| --- | --- | --- |
| R4 | Two-slot reuse; old, foreign, copied and out-of-range locators; occupied/full rejection retains incoming owners; ceilings 0/1 force retirement; unrelated live slot survives | Six literal-controlled cases, 30 commands, existing independent Bend store model on Bun/native; shader validation only |
| R6 | Capacities 0/1/2; rejected full offer preserves queue and owner; duplicate offer; physical reversal; zero quantum; suspend/wait/wake/complete; invalid and unsupported commands; all three phase snapshots | Ten literal-controlled cases, 32 commands, independent Bend frontier model on Bun/native; eight filled laws and seven CPU semantic mutants killed; shader validation only |
| Device mutations | Retain extracted payload, ignore arena/generation, generation wrap, consume full-queue owner, duplicate compaction, change destination, read before publication, advance zero quantum | Nine WGSL mutants typecheck and create pipelines; hardware kills are **unrun** |
| R5 | General affine captures and n-ary joins | Deferred; no owning environment, Data lifetime, attempt identity or cancellation/drop implementation yet |

The proof boundary is explicit: two quantified equations (zero slice and unsupported-slot preservation) and six
concrete normalization laws. Reusable model records describe observed ownership;
they do not by themselves establish generic affine payload storage. The GPU
scheduler and two task invocations are bounded feasibility code, not a production
allocator or throughput result. Source compilation and Knot evaluator/Wasm
execution of these new runtime records are not implemented.

The executor's Metal adapter request returned null inside its sandbox. The
coordinator then ran the retained commands on the host adapter (Apple M5 Max,
`metal-3`, not a fallback): all 16 R4/R6 device cases pass, all nine WGSL
mutants are killed, and the old 38 cases agree semantically before (`185b7d5`)
and after the change. See the
[runtime receipts](../research/adaptive-tasks/runtime/README.md). The rows above
are therefore device-qualified for the bounded probe domain; the Device mutations
row's "unrun" note is superseded by that record.

Plain `check.py`, `gpu/check.mjs` and `codegen/generate.py` replays now write under
ignored `.local/adaptive-tasks/`; `--out-dir` selects another destination and
`--update-receipts` explicitly refreshes retained artifacts. Device receipt
comparison preserves fixture identity, case parameters, results, ownership,
bounds and deterministic phase observations, excluding raw state hashes and
logical-worker movement. Historical receipts retain their original provenance.

R5 must wait for a mixed-field owning environment and explicit attempt identity:
a stale completion after cancel/replace can target a still-live join generation.
Qualify that distinction with rejection retaining the incoming owner, then
right-before-left noncommutative delivery and n-ary completion exactly once.
R3/R7 remain necessary for reusable captures and suspended/join roots; scalar
payloads and generation checks cannot stand in for their lifetime evidence.
