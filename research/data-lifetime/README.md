# Data lifetime decision packet — r3r7

**Recommendation for coordinator/user decision: adopt unique Type objects and
reference-counted immutable Data (B) for milestone 1.** Reclamation must be part
of that increment's owned-storage acceptance. The fields Wasm bump arena is an
interim construction path and does not close lifetime or reclamation.

Both policies satisfy this bounded executable model. B preserves sharing on
compiler-shaped graphs and replaces repeated tree copies with root acquires.
A has a smaller record layout and simpler unique-owner cleanup; its cost grows
with the **expanded value**, even when the source graph is small. Keep A as a
conformance/control model. Do not add a hybrid representation before measuring
the integrated emitter; this packet does not select one.

This is a decision experiment, not a heap implementation in `src/`, a policy
adoption, or a milestone pass. `Heap` is reusable graph metadata with scalar
proxies for Type owners. The affine `Store` wrapper enforces threading, but its
public constructors do not make the metadata an unforgeable owning capability.
The existing generic owning-store qualification remains a separate prerequisite.
Neither candidate has run as a lifetime implementation in Knot Wasm or on GPU.

## Reproduce and inspect

```sh
export BEND_NO_TELEMETRY=1
python3 research/data-lifetime/check.py
bun --no-env-file .toolchain/bend-2.0.29-574b6d3/bend2/main.ts research/data-lifetime/PROOF.bend
```

The gate uses the pinned seed directly with `--no-env-file`, native and Bun
builds, and the independent Python model. It performs no network operation.
Build products go to `.local/data-lifetime/`. [SPEC.md](SPEC.md) fixes the
operational contract; [expectations.json](expectations.json) fixes hashes of
the independent oracle, trace generator and initial literals **before** the
Bend implementation. Three additional failure traces have separate, literal
expectations in [extra-traces.json](extra-traces.json). No initial expectation
was changed to match Bend output.

- [model.bend](model.bend): one obligation graph, two share operations; explicit
  postorder copy machine and resumable release stack.
- [reference.py](reference.py): independent mutable dictionary/recursive-copy
  model, transactional snapshots and whole-graph invariants. It calls no Bend
  operation. This is a research oracle, not host implementation of Knot.
- [traces.py](traces.py): fixed-seed trees, lists, reconstruction, shared subterms
  and holder transitions, including frame/join cancellation and reader completion.
- [LAWS.bend](LAWS.bend), [PROOF.bend](PROOF.bend): 20 filled equations. Complete
  proof entry prints `All terms check.`; see [LAW_REVIEW.md](LAW_REVIEW.md) for
  the exact, deliberately bounded theorem claims.
- [receipts/gate.json](receipts/gate.json): input/artifact hashes, measurements,
  semantic mutant witnesses and source differential results. Compressed
  [native](receipts/native.txt.gz) and [Bun](receipts/bun.txt.gz) transcripts retain
  every actual state, not just an assertion summary.
- [receipts/trust.json](receipts/trust.json): both complete seed check closures
  have zero holes; generated model execution requires only `IO.print`.

Fresh result: **105 traces per candidate, 1,697 transitions per candidate per
lane, 6,788 complete-state comparisons**, 20 literal checks, 1,691 cross-policy
value/holder comparisons, 20 filled laws, 5 quantity controls and **16
type-correct semantic mutant kills**. Four deliberate resource divergences are
recorded separately: copy capacity twice, count ceiling and shared-open count
overflow. Invalid and Unsupported observations do not diverge between policies.
Every completed generated workload and both frame/join witnesses end with no
live cells, holders, pending work or readers.

The four source fixtures cover tree reuse, list-tail reuse, mixed Type/Data
reconstruction and shared-parent opening. Their literal constructor results
agree with the pinned **interpreter** (4 calls) and Knot's independent evaluator
(8 native/Bun calls). The current checkout rejects their Wasm compilation with
`Unsupported check constructor-fields` (8 observations), preserving an existing
output marker. This is an explicit missing differential lane. Generic store
models themselves exceed this checkout's Knot profile; no seed-built model is
presented as a Knot-built one.

## Measured policy work

Each row runs the same command trace under both candidates. A word is four bytes
in the proposed Wasm/GPU mapping. Peak includes payload and B's one RC word per
Data record. Roots, pending-work storage, free-list/generation metadata, copy
staging representation and host/runtime overhead are separate costs. The table
uses successful allocations; its numbers are measured committed logical work,
not RSS, reserved Wasm pages, elapsed time or a speedup.

| Trace | Peak words A / B | Allocations A / B | Copied words A / B | Edge visits A / B | RC acquire / release B | Cleanup steps A / B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| List: 64 links + terminator; two holders | 388 / 259 | 130 / 65 | 194 / 0 | 192 / 64 | 1 / 66 | 130 / 66 |
| Tree: 63 records; five holders | 940 / 251 | 315 / 63 | 752 / 0 | 558 / 62 | 4 / 67 | 315 / 67 |
| Shared subterm: eight successive `pair(x,x)` constructions | 1,532 / 43 | 511 / 9 | 1,498 / 0 | 1,004 / 16 | 8 / 17 | 511 / 17 |
| Unique Type wrapper: 64 opens/rebuilds around one Data leaf | 5 / 6 | 66 / 66 | 0 / 0 | 65 / 65 | 0 / 1 | 2 / 2 |

All 24 increasing-size measurement traces and all ten counters are retained in
the receipt. The shared-subterm result is **6,128 versus 172 logical peak bytes**;
the unique wrapper shows B's metadata cost when sharing brings no benefit.
Copying cannot retain the DAG: every reuse makes an independent tree. RC stores
each graph node once and counts its repeated incoming edges. A shared B parent
must acquire children when opened; a uniquely held parent transfers them.

The counters include construction/free actions, copy words, edge visits,
acquires/releases, cleanup steps, live/peak words and peak cleanup stack length.
They exclude list-map scans, validation, transaction rollback work, root tables,
worklist allocation and seed GC. Failed transactions restore all published
counters, so those rows do **not** measure wasted tentative copy work. Full
physical cost must be instrumented in the emitter, including allocator metadata
and the entire bounded staging reservation. These are operation/space trends,
not constant-time or throughput evidence for this list-based Bend model.

`bench/` currently builds Knot's enum compiler and times nullary Wasm exports.
It has no stateful trace driver or heap-counter interface, and cannot compile
these generic models. Its suite contract therefore does not fit this experiment.
After integration, add the identical traces to `bench/` with correctness guards,
warmup and samples; keep logical counters separate from measured Wasm time and
page high-water marks. No benchmark framework file is changed here.

## Emitter and record mapping

Target payload layout remains **`knot-fields-wasm-1`: `[tag][live slots]`**. The
model's scalar tag is one live scalar slot; children are live reference slots.
Nullary/scalar unboxing is an optimization outside this experiment. Erased fields
have neither a word nor a retain/drop action. Layout descriptors retain declared
kind, quantity and each live edge's role; scalar slots must never be traced as
pointers. Slot width is a target decision, not the source binder's lexical level.
Model identities are not byte offsets; the model's zero sentinel does not reserve
address zero in the field ABI.

| Obligation | A: copied Data | B: unique Type + counted Data |
| --- | --- | --- |
| Allocate | Reserve one owned record; move input edges; publish last. | Same, initialize Data count to one. Moving an edge is not an acquire. |
| Data occurrence beyond a transferred use | Emit a typed recursive clone; pre-reserve all destination storage or retain an explicit rollback journal. | Checked `retain` of the root before publishing the new holder. Overflow is Exhausted and preserves inputs. |
| Match/take | Load fields, invalidate/free the parent, transfer children. | Type or count-one Data uses that path. Shared Data retains each child edge before releasing its parent reference; reserve/count-check the whole operation before publication. |
| Drop/last use | Push every owned child onto a resumable release stack. | Decrement Data; only zero walks its descriptor. Type always walks its unique owned children and releases Data edges. |
| Record metadata | Size/layout/free-list state outside the payload. | Same plus an RC side table or prefix **outside** `[tag][live slots]`; adding an inline count without versioning would break existing offsets. |
| Failure | Return unchanged owners; free unpublished copies or retain resumable staging. | Preflight all count increments, including duplicate child edges, or roll back all provisional acquires. |

The emitter cost for B is concrete: checked acquire/release helpers; a zero-count
descriptor walk; a persistent cleanup worklist; explicit move/share/drop decisions
on locals, arguments, returns and branch exits; unique/shared opening; and
capacity/overflow failure paths. Saved frame and join slots are holders too.
Returning a locator or copying an `i32` does not register a holder. A reconstruction
recipe in compiler metadata is not another root. Unused affine locals must still
transfer their owned edges into cleanup. Retain elision and last-use optimization
come after these paths agree with the independent evaluator.

Both candidates also need a reclaiming allocator. Wasm memory generally retains
its page reservation: logical freeing makes cells reusable, not smaller memory.
Use layout/size-aware free lists and preserve the owned/flat-store freshness
discipline; this model's monotone identities do not qualify slot reuse, arena
issuance or generation retirement. Reclamation needs bounded work storage and
an explicit continuation on exhaustion, not recursive calls on an unbounded
native/Wasm stack. The model assumes sufficient space for root/work metadata;
its real allocation and failure path remain emitter obligations.

## GPU records (D5)

The campaign chooses a device task interpreter over records first; specialized
WGSL follows. Map holder slots to caller/task/frame/join records. The existing
[device protocol](../adaptive-tasks/DEVICE-PROTOCOL.md) supplies immutable phase
inputs, one writer per record and dispatch-separated publication. It qualifies
a unique-parent task tree, not a shared Data heap.

For A, each duplication command reserves and fills an independent record tree.
Allocation failure must preserve the source holder and staging owners; a clone
too large for one quantum needs explicit copy frames. It avoids shared RC writes,
but the eight-level trace already shows expanded storage/work. Type captures
still transfer to one destination. A copied container does not justify copying
an owned Type child.

For B, task records hold counted Data edges and unique Type transfers. A bounded
first design can emit acquire/release deltas into per-task buffers, publish them
at a dispatch boundary, and apply them with one owning writer per object before
the next snapshot becomes readable. An atomic-count implementation is another
candidate, **not qualified here**: checked increments must not wrap, a reservation
counter does not publish payload words, and last-release cleanup must not race
with an acquiring or submitted reader. Failed delta publication retains the
task/input owner. Partial joins must keep both the delivered result and saved
parent continuation rooted; attempt freshness is separate from object freshness.

Both mappings delay physical reuse until **all** submitted readers/snapshots
acknowledge completion. The model uses a conservative global reader barrier:
logical release is allowed, physical take/reclamation waits for the final ack.
This is executable sequential evidence for the obligation, not GPU synchronization
evidence. Root omission, early reuse, lost cleanup and duplicate disposal mutants
are killed. Actual scheduling, queue capacity, stale attempts and cancellation
publication belong to the gpu-runtime increment's device probes.

Keep storage flat in `u32` words. If the GPU profile uses the dependency contract's
`(arena,slot,generation)` locators, charge three words per locator explicitly;
do not reuse this table's one-word pointer totals or assume packed arrays of
`vec3<u32>`. Mixed-width layout/byte transport and canaries must be qualified
separately on the actual device. The recommendation compares policy growth;
it does not claim identical CPU and GPU byte counts or operation counts.

## Limits and next increment

The trusted trace language is immutable, acyclic, binary-arity and finite. For
either policy, new parents point only to older children; cloned children are
allocated before their parent. The host invariant checks this birth order after
every step. `cycle`/backpatch is Unsupported. This construction argument is not
a mechanized no-cycles theorem for future closures, mutable arrays or effects.
Model inputs bound capacities/counts and work; U32 counter overflow on arbitrary
unbounded traces is not qualified. Measured policy IDs are 0/1, word capacities
0–100,000, and count ceilings 1–100,000; `initial` is a trusted model constructor,
not a validator for malformed limits or snapshots. There are no custom disposer closures, restore
tickets, arbitrary host pointers, concurrent writers or physical slot reuse.

R2/R3/R7 are tested at the graph-model boundary, with R5 holder composition.
General runtime refinement, global arena authority, disposer-capture cleanup,
task-attempt freshness, device readers and bounded worklist allocation remain
open. No general compiler correctness, lifetime theorem or GPU pass is claimed.

Next: obtain coordinator/user disposition, then integrate B behind the existing
field payload ABI. Preserve the 20 literals and trace source expectations;
extend the differential to actual Knot-emitted Wasm memory and logical ownership
observations. Instrument full physical space/work, add type-correct emitter
mutants, and replay the frame/join/reader traces on real GPU records. Gate
milestone closure on reusable storage after last release and reader completion.

All 11 requested existing gates pass; exact counts and the resolved parser-cache
failure are recorded in [receipts/regression.json](receipts/regression.json).
Their original tracked receipts are restored because this experiment does not
alter their contracts or implementations. Pre-existing compiler receipt source
hash drift is left to the coordinator, as recorded in campaign state.

Offline [style preflight](receipts/preflight.json) parses 137 declarations in 8
files with zero provider requests. Composition is available (25,109 / 48,000
bytes). **15 declaration contexts are truncated**: 11 caller/byte limits and 4
helper limits; those same 15 lack complete supporting-role context. Compression,
Delight, memetic identity, Anticipation and Payoff have **no live ratings** here.
This is not a style pass. Live Perch review and context qualification remain with
the coordinator; no correct implementation was changed to chase an advisory score.

No commit was created: the sandbox denied creation of the worktree's Git
`index.lock` outside the writable root. The increment is complete in the working
tree, with explicit-path handoff instructions in [HANDOFF.md](HANDOFF.md).
