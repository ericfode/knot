# Checked binary-join contract

This directory is a research artifact, not a released package or implemented
runtime. It supports the [execution-model laws](../../docs/EXECUTION-MODEL-LAWS.md)
and [architecture case](../../docs/EXECUTION-MODEL-CASE.md).

## Contract and domain

`model.bend` is an abstract sequential binary join over arbitrary reusable
`Data` payloads. Its states are `JOpen`, `JLeft`, `JRight`, `JReady`, and `JTaken`.
Successful deliveries fill source-ordered slots. A duplicate preserves the
earlier payload and returns rejection. Taking an incomplete join waits; taking
a ready join returns its ordered pair and transitions to taken; a further take
is denied. No partial failure, cancellation, scheduler, allocator, or weak
memory model is hidden in these definitions.

The one-time-take equation assumes the caller threads the returned state.
Because this abstract state is `Data`, a caller could copy an old `JReady` value
and evaluate `take` on that old snapshot again. Preventing that in a real runtime
requires the single-owner store/handle discipline; this model does not enforce
linear use of its own history.

All five control states are reachable in an inhabited U32 instance, with 7 and
9 as distinguishable payloads. The laws quantify over arbitrary `Data` types
and payloads. Empty types also satisfy some equations trivially, but the claims
do not depend on an uninhabited premise: runtime witnesses exercise every state.
Payloads are observed as ordered pairs, not commutative sums.

## Evidence

`LAWS.bend` states 18 transition/composition equations. `PROOF.bend` fills each
with definitional equality. These are checked equations with free payloads,
not proofs by testing a finite set of U32 values. They do not constitute an
induction over all execution traces or a refinement of a concurrent algorithm.

The equations specify the complete control transition table; this proximity to
the abstract model is intentional. Their use for a future optimized join is
as an independent observable contract, not as proof of that future code.

| Operation | Laws | Distinguishing runtime evidence |
|---|---|---|
| `left` | first_left, finish_left, duplicate_left, ready_left, taken_left | Right arrives first; duplicate left=9 cannot replace left=7. |
| `right` | first_right, finish_right, duplicate_right, ready_right, taken_right | Left arrives first; duplicate right=7 cannot replace right=9. |
| `take` | take_open, take_left, take_right, take_ready, take_taken | Wait in incomplete states; yield (7,9); deny a second take. |
| `state` observation | completion_order, completed_payloads | Both arrival orders preserve source slots (7,9). |
| `after_take` observation | second_take | The returned state is consumed, not ready again. |

Ten fixture observations are compared with an independently written expected
transcript on reference JS and native C execution. The laws cover ready/taken
delivery branches that the ten runtime observations do not separately exercise.
No runtime coverage claim goes beyond that list.

Four mutations each typecheck on their own, fail a named law, and change a
runtime observation: swapped slots, duplicate overwrite, repeatable take, and
premature completion. Typechecking failure in a mutant model is a harness
failure, not a successful semantic kill. Mutants only exist in temporary copies.

## Reproduce

From the repository root:

```sh
python3 research/execution-models/check.py
```

Prerequisites: the existing pinned reference archive described in
`docs/PACKAGE-CAMPAIGN.md`, Bun, Python 3, and the native C toolchain used by Bend.
The script makes no network requests. It typechecks the proofs, executes the
fixture on both reference paths, and runs the four mutations. It writes
`evidence.json` only after every check passes. If a future run fails, an older
receipt is not current evidence: compare its recorded hashes and timestamp.

`reference-hashes.json` records four compiler/checker/Base files verified byte
for byte against official upstream commit
`574b6d39a235b539eb19a5c532993a0abb3d11ad` on 2026-09-26. The runner rechecks those
local hashes. This is a core-file pin, not a claim that every foreign handler or
the host toolchain is reproducibly verified. The compiler, checker, primitive
semantics, and host build tools remain in the trusted base.

Python only orchestrates commands, temporary mutations, output comparisons, and
receipts. Protocol definitions, proof statements, proofs, and executed witnesses
are all in Bend.

## What remains unverified

- Concrete storage/queue refinement and arbitrary-trace invariants.
- Affine closure/handle payloads; the model deliberately uses `Data`.
- N-ary joins, failure propagation, cancellation, and resumable exhaustion.
- Concurrent publication/reclamation and task movement between workers.
- Wasm, WGSL/WebGPU, actual-device correctness, and performance.

See the [dependency handoff](../../docs/EXECUTION-MODEL-DEPENDENCIES.md) for the
contracts needed by the package-building chat.
