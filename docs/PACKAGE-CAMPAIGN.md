# Compiler-support package campaign

Completed 2026-09-26: all six selected packages have verified remote releases.
See [published hashes, imports and evidence](PACKAGE-RELEASES.md) and
`packages/releases.json`. The coordinator heartbeat is paused.

Requested 2026-09-26 by the user: build a separate package per priority component,
improve Perch as the work exposes mistakes, verify substantive non-vacuous laws,
then publish completed packages to Bend's package hub.

The current scope is the six priority foundations from the inventory. The
coordinator asked whether the user wants the broader missing-library inventory;
absent a broader selection, conditional optimizers and additional containers
are not silently added to this campaign.

## Ownership and dependency order

| Package directory | Deliverable | Initial dependency plan | Reasoning |
| --- | --- | --- | --- |
| `packages/vec` | Checked growable vector, logical length/capacity, slices | Base only | Extra high |
| `packages/source` | Indexed source storage, cursor/checkpoint/span, line index | Vec; specify encoding/offset units | High |
| `packages/output_builder` | Ordered chunk builder and linear output assembly | Base lists initially | High |
| `packages/int_map` | Persistent U32 map with pointwise combining merge | Base only | Extra high |
| `packages/symbols` | Stable string interning with reverse lookup | Vec; Base Map may bootstrap lookup | High |
| `packages/term_store` | Stable node/cell storage and explicit memo state | Vec; IntMap only if actually needed | Extra high |

Chats share one checkout but have disjoint ownership, described in
`packages/AGENTS.md`. `packages/threads.json` records the actual created chat IDs.
The coordinator owns this manifest, root scripts, common Perch law rules, and
integration bookkeeping. Do not overwrite the active compiler-planning work.

Publish dependency interfaces early. Dependents may work on models/laws/tests
before dependencies are ready; integration and release wait for a verified
dependency interface. Release imports use the dependency's published content
hash, never an untracked sibling path. The publication order is Vec before
Source/Symbols/TermStore; OutputBuilder and IntMap can finish independently.

The selected [Wasm/WebGPU backend](WASM-WEBGPU-BACKEND.md) adds two concrete
requirements within this scope: OutputBuilder needs a raw-byte path distinct
from text/codepoints, and TermStore must never expose exhausted/incomplete memo
work as a completed value. Those requirements were sent to the owning chats.
Vec's Data-only elements suit immutable syntax; affine runtime payload storage
needs a separate ownership protocol. LEB128 encoding, bounded FIFO/frontier
queues, continuation records and exactly-once joins are follow-on requirements
from execution-model research, not additional chats silently added here.

The detailed [execution-model handoff](EXECUTION-MODEL-DEPENDENCIES.md) also
requires reproducible emission. IntMap specifies a deterministic
least-significant-bit-first traversal, not numeric key order. Symbols assigns
IDs in first-intern order within one table; compiler callers must choose a
deterministic insertion order or use a separately specified canonical remapping
before emission. Namespace and lowering-origin preservation belong to the
compiler's use of these APIs. None of these host package releases establishes
Wasm/GPU execution or a concurrent runtime ownership protocol.

## Accepted runtime direction and follow-on ownership

On 2026-09-26 the user selected **adaptive continuation tasks** in Compiler
Planning: "Adaptive continuation tasks it is then". This is an accepted design
decision. The authoritative case is [EXECUTION-MODEL-CASE.md](EXECUTION-MODEL-CASE.md).
Sequential Wasm is the initial compiler execution path; bounded GPU execution
with dispatch-separated task exchange is the working WebGPU design to validate.
Fixed placement remains a comparison baseline. Interaction-net machinery is
outside the selected implementation path.

The next component boundaries, in priority order, are:

| Separate component | First contract/model increment | Defining observations and witnesses |
| --- | --- | --- |
| Indexed owning slot store | Refine the checked single-slot protocol into indexed affine storage. A failed put returns both the original store and uninserted owner; take invalidates the slot. Specify arena lifetime and any eventual generation reuse. | Two takes cannot acquire one payload twice; failed put loses no payload; foreign, stale and out-of-range handles fail without changing unrelated slots. |
| Continuation, frame and join records | Capture code tag, owned environment, frames, checkpoint and logical join destination. State suspension/resumption and transfer against a sequential reference model. | Resuming preserves future results and effect position; transfer invalidates the old executable owner; reversed child arrival still yields ordered results; duplicate delivery and repeated completion fail. |
| Bounded frontier/queue | Refine ordered contents against an independent list model, with explicit capacity and transfer into/out of the owning store. Preserve logical destination and join slot through compaction or reordering. | Empty/full failure preserves queue and payload ownership; FIFO order and length agree where promised; every obligation appears exactly once across ready, running, suspended and waiting states. |
| Checked layouts and codecs | Specify checked size/offset/alignment arithmetic and explicit record encodings. Consume OutputBuilder's published raw-byte path; add ULEB/SLEB as separate algorithms. | Reject overflow, invalid tags and truncated records; round trips cover field and 7-bit/sign boundaries; failed allocation preserves owned inputs. |

These are separate follow-on ownership units. `packages/threads.json` records
only the six completed package assignments. Their published Data contracts stay
the compiler-library boundary; an ID in Vec or TermStore does not confer affine
runtime ownership. New implementation assignments and runtime release decisions
belong to the follow-on work, not the paused package-publication heartbeat.

**Completed probe handoff, reviewed 2026-09-26:** Compiler Planning
(`01a0dea7-91b5-7480-b80a-7fe9584f9966`) retains ownership of
[`research/adaptive-tasks/`](../research/adaptive-tasks/README.md). The coordinator
matched all 16 source hashes in its [deterministic receipt](../research/adaptive-tasks/receipts/checks.json),
the linked [device receipt](../research/adaptive-tasks/receipts/gpu.json), and all
14 source/retained-receipt pairs in the combined [research Perch audit](../research/perch-audit.json).
This handoff checked existing evidence; it did not rerun unchanged experiments.

The recorded increment has 12 checked Bend laws, including arbitrary-budget
composition over full affine states; two invalid ownership uses rejected in the
quantity phase with a valid neighboring control; and five type-valid Bend
semantic mutants rejected by laws and runtime observations. The device receipt
records 38 WebGPU runs and 1,713 dispatches on a non-fallback Apple M5 Max/Metal
adapter, including agreement with the independent Bend result oracle and
explicit resource failures. Three valid WGSL mutants fail result agreement.
The [combined research Perch report](../research/PERCH_REPORT.md)
records 88 checks and 14 provider responses from `jev-1.13.0`, with no findings
meeting reporting floors. That advisory review covers Bend and law packets;
it does not cover WGSL, JavaScript or Python.

The [device protocol](../research/adaptive-tasks/DEVICE-PROTOCOL.md) relies on
immutable phase snapshots, one writer per record, and exactly one parent per
child. Parent capture and child retirement use the same prior snapshot; this
rule does not extend to shared DAGs. The prototype never reuses slots within a
run and destroys buffers after queue quiescence. Reusable handles still need
arena/generation validation, an explicit wrap policy, and reader-quiescence
contracts. Frontier reservation is not same-dispatch payload publication.
The fixed 48-byte operation and 64-byte task layouts are probe contracts,
not a general checked layout implementation.

These results establish bounded tree-task feasibility with handwritten WGSL
and a native Node host. Wasm hosting, Bend-source lowering, generic affine
continuation storage, a general heap, performance, and full CPU/device simulation
remain open. Use [E2, E6–E8 and G1–G4](EXECUTION-MODEL-LAWS.md) and the
[detailed component handoff](EXECUTION-MODEL-DEPENDENCIES.md) for subsequent
refinement and publication obligations. The six published package contracts
retain their existing owners. Additional runtime assignments and releases are
separate follow-on work; the completed campaign heartbeat stays paused.

## Build reference

Use upstream Bend **2.0.29**, revision
`574b6d39a235b539eb19a5c532993a0abb3d11ad`, through
`scripts/bend-reference`. It runs the pinned source with the existing Bun runtime;
it does not upgrade another project's compiler. This is the package campaign's
build reference, not Knot's eventual language compatibility decision.

The source is kept in ignored `.toolchain/bend-2.0.29-574b6d3/`. Record the
reference and dependency versions in each release. Avoid unnecessary dependence
on new/unsafe Base features. Existing 2.0.16 compatibility can be measured if
useful; do not claim it without a check.

To restore a missing reference, download the [pinned upstream source archive](https://codeload.github.com/bendlang/bend/tar.gz/574b6d39a235b539eb19a5c532993a0abb3d11ad)
and extract its contents into that directory (with the archive's top directory
removed). Do not overlay an existing toolchain. The SHA-256 of
`bend2/base.bend` must be
`22eea83911e2395f63594fea7c10ac0c1e5b548251681fc97cd7667e0eb7031b`;
`scripts/bend-reference version` must report `bend 2.0.29`. Bun must be installed.

## Completion contract

Implement the component in Bend, provide a minimal runnable consumer and docs,
and satisfy [the law quality gate](LAW-QUALITY-GATE.md). Core properties include:

- Vec: logical bounds, contents/order across growth, push/pop composition,
  set/get and preservation, and explicit capacity/overflow failures.
- Source: original content preservation, cursor progress/rewind, exact span
  extraction and offset/line round trips, EOF and invalid-position behavior.
- OutputBuilder: emitted content equals the ordered fragment sequence, empty
  identity and composition, retained bytes/code points, and linear assembly.
- IntMap: lookup after set, unrelated-key preservation, replacement/deletion,
  persistence of previous versions, and merge semantics including noncommutative
  combiners. Include usage-quantity add/join examples for the compiler.
- Symbols: equal strings share an ID; distinct strings do not; reverse lookup
  recovers the original; IDs remain stable within the documented table lifetime.
- TermStore: stable IDs and stored values, preservation across growth/updates,
  scoped ID validity, and explicit pending/completed/failed memo transitions.
  Do not turn partial evaluation or fuel exhaustion into a completed value.

No full compiler, normalizer, generic hash-table framework, or backend is required
inside these bounded packages. Record cross-package design needs instead of
expanding silently. Code must be suitable for a future compiler written in Bend.

## Perch improvement

The shared eight law rules are installed in `.perch/rules/laws.yaml`. Each author
adds useful, narrow package rules in its owned rule file, with paired and held-out
controls. Give Perch bounded self-contained law review packets. Preserve exact
coverage and calibration evidence; make deterministic regression tests for real
defects. Live Perch was unavailable at campaign setup; subsequent owner reports
record live review, including the [research audit](../research/PERCH_REPORT.md).
Retain exact source/rule identities and coverage for each review. An unavailable
provider is neither a semantic pass nor a blocker to otherwise verified work.

## Publication

Publication to the official BendHub is explicitly authorized once gates pass.
Use the pinned CLI's `--publish` without a friendly-name argument unless named
credentials are already available and naming is wanted. Anonymous content-hash
publishing does not need `~/.bend/bender.json`.

1. Freeze implementation, model, laws/proofs, consumer and dependency pins.
2. Inspect the actual `pkg_files` closure from the pinned CLI or an equivalent
   exact dry run: only intended source and license files may be uploaded.
   Include the laws/proofs via the chosen entry's imports; preserve third-party
   licenses. Original code uses explicit MIT-0 instead of an implicit default.
3. Run all promised proof, conformance, semantic mutation and performance gates
   against that exact release state. Record outcomes and explicit limitations.
4. Run `scripts/bend-reference <release-entry.bend> --publish`, retain output,
   and verify the returned hash equals the expected content identity.
5. With a fresh `BEND_LIB` cache, import that returned hash in a consumer, build
   and run it, and verify the output. Verify remote files/manifest as appropriate.
6. Write `RELEASE.json` and STATUS.md with the hash/import, source closure,
   compiler/dependency versions, license and gate/fresh-consumer receipts.

The hub is the package repository requested here. This is not a request to push
unrelated Git changes or open an upstream pull request. Root Git state currently
includes concurrent planning/tooling work; keep it intact.

## Coordination

Use STATUS.md as the durable owner-written state. The coordinator may inspect
chat progress and send necessary follow-ups within this user-requested build
and release workflow. Do not message unrelated chats or external people. Report
only meaningful changes: a ready dependency, a gate failure, a publication, or
required user action. Completion means every selected package has a verified
remote consumer, not merely that its chat is idle.

The `complete-bend-package-campaign` heartbeat checked every 15 minutes and
resumed idle dependents when their blockers were resolved. It was paused after
all six verified remote releases. Build chats performed their own validation
and publishing; the coordinator verified receipts and closed dependency handoffs.
Local progress cursors live in `.local/package-campaign/state.json`; they record
chat observations, not independent proof or release evidence.
