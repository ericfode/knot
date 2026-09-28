# wasm-owned handoff

`campaign/wasm-owned`, based on `bfcb4aa`. The increment adds
`knot-owned-wasm-1`; integration and live Perch review belong to the coordinator.
No push, merge, rebase, package change, or existing gate assertion change is
included. Existing shared receipts remain for coordinator refresh.

The new runtime uses exact live-slot size classes, unique Type transfers,
counted immutable Data, and a bounded iterative release stack. Continuation
liveness lowers checker quantities into share, move and release. The shared
emitter has only profile dispatch; 116 frozen checks preserve Enum/Fields bytes.
The ordinary host adapter distinguishes Exhausted, InternalFailure and HostFailure.

The heap reserves 131,072 bytes, including all heads and release frames. Four
recursive calls allocate 131,072 cells over their lifetime, peak at 32 live
cells, and return with live 0 and pending 0. The cell-region high-water mark is
636 bytes. One full call exhausts the arena control. Logical freeing enables
reuse; it does not shrink the reservation.

## Validation

`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1` exited **0**: **15/15 gates passed** in **445.383793 measured seconds**. The [complete receipt](receipts/regression.json) records commands, source/dependency identities, counts and receipt drift. `npm run -s gates:verify` also exited 0: [18 tests and six semantic mutants](receipts/gates-verify.txt). The focused manifest check passed 20/20 tests.

| Gate | Exact passed coverage |
| --- | --- |
| `frontend` | 14 fixtures; 28 lane observations; 24 boundaries; 4 mutants |
| `checker` | 49 fixtures; 98 lane observations; 10 budgets; 2 bound cases / 16 observations; 7 mutants |
| `structural` | 16 fixtures; 64 lane observations; 4 bounds; 7 mutants |
| `fields` | 40 fixtures; 240 lane observations; 36 budgets; 6 host boundaries; 2 bound cases / 12 observations; 9 mutants |
| `wasm` | 25 fixtures; 90 reference calls; 2 execution lanes; 64 rejections; 44 boundaries; 7 mutants |
| `wasm-trust` | 3 entries; 0 proof holes |
| `fields-trust` | 4 entries; 0 proof holes |
| `structural-trust` | 2 entries; 0 proof holes |
| `owned-store` | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| `flat-store` | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes; 9 mutants |
| `recursion` | 19 fixtures; 3 mutants |
| `fields-wasm` | 8 fixtures; 30 boundaries; 4 mutants |
| `census` | 38 source files; 593 declarations; 40 classes |
| `lint:verify` | 127 tests; 8 law-rule wiring controls |
| `owned-wasm` | 29 positive fixtures; 64 core seed observations; 112 ordinary evaluator observations + 2 extended values; 112 Wasm observations; 29 compiler-lane byte agreements; 116 legacy byte checks; 16 negative pairs; 24 boundaries; 24 allocator states; 20 runtime witnesses; 43 laws; 5 mutants / 10 lane kills |

Of 81 compared artifacts, 63 were identical, 8 volatile-only and 10 semantic. Existing semantic drift is source/build inventory identity, with unchanged fixture observations; the new owned receipt lacked a tracked baseline at export. Shared receipts were not refreshed.

Earlier [four-worker](receipts/attempt-host.json) and [two-worker](receipts/attempt-host-two-workers.json) attempts retained native compiler discovery/process-budget failures. Isolated Clang discovery passed 64/64 probes. The sequential run passed without changing source, assertions, or timeouts; this does not establish the cause of the intermittent host fault.


Categories overlap; they are not a single additive assertion count.
The 112 ordinary evaluator observations include 110 values and the two original
`fields-deep-call` default-parser-budget Exhausted observations. Two additive
runs use the fixture's already frozen compilation budgets and return `On{}`.
Thus all 56 positive source calls have seed/evaluator/Wasm value agreement in
both compiler lanes. The 24 boundary probes separately include four seed and
four evaluator observations.

The complete proof entries print `All terms check.`: 17 concrete heap laws in
`src/heap-PROOF.bend`, 13 ownership laws in `src/ownership-PROOF.bend`, and 13
independent semantic model laws in `model-PROOF.bend`. These are checked model,
layout and instruction equations plus finite execution conformance, not a
universal source/heap/Wasm refinement theorem. [Law packet](LAW_REVIEW.md).

The initial [D7 freeze](expectations.json) binds literal expectations, source
hashes and old module bytes before owned emission/runtime behavior. Its
[seed replay](receipts/reference.json) has 63 observations. Additive freezes
retain shared boxed children, reserved export rejection, source heap exhaustion,
and the larger-budget evaluator; no original expectation changed.

## Fixtures and mutants

The new source fixtures are `unused-owned`, `branch-cleanup`, `share-live`,
`recursive-reuse`, `release-chain`, `shared-boxed`, `reserved-export` and
`heap-overflow`. Existing fields/recursion programs and four lifetime packet
controls are included. The independent allocator model supplies 12 full-state
observations per lane; ten actual runtime witnesses per lane include a complete
3,277-cell chain and duplicate-child count overflow with unchanged memory.

The five seed-type-correct, valid-Wasm mutants are killed in both lanes:

- Missing release leaves five cells live after an enum result.
- Double release produces InternalFailure.
- Omitted share corrupts the retained value and incoming count.
- Premature reuse corrupts the same independently fixed retained value.
- The off-by-one stack bound admits two frames under a one-frame limit.

The [independent review](REVIEW.md) covers stacked arguments, nested branch
cleanup, shared boxed edges, overflow preservation and the tail-call threshold.
The [wide-tail failure](receipts/attempt-wide-tail.json) remains HostFailure
history. The [manifest failure](receipts/attempt-manifest.json) is superseded by
closed source groups and moving the independent model laws into the test packet.
All 43 equations remain; [176 artifacts stayed identical](receipts/proof-split-artifacts.json).

## Style preflight

Offline [preflight](receipts/preflight.json) covers every changed/new Bend file:
**342 declarations in 24 files**, zero empty/unranked files and zero provider
requests. Exit 3 records **39 structural blockers**: 38 truncated declaration
contexts and an unavailable composition. There are 77 supporting-role context
gaps. Truncation reasons overlap: 12 caller/byte, 14 file-count and 16 helper-count
limits. Composition is 153,662/48,000 bytes, with 50 missing collaborator and 124
nonlocal-import references. No live Compression, Delight, memetic identity,
Anticipation or Payoff ratings exist; this is not an automatic style pass.

## Benchmark

The [benchmark](../../bench/OWNED.md) compares two allocation-heavy workloads,
two profiles and two compiler lanes with seven samples each. Median owned cost
is **2.34–2.70 times** arena cost in the retained session. Reserved memory is
128 KiB versus 64 KiB. The acceptance benefit is reclamation and bounded reuse;
there is no speedup claim. Instantiation is outside the timer, while host loop,
export invocation and result checks are included.

The [timing receipt](receipts/benchmark.json) is preserved with its exact
[measured gate snapshot](receipts/benchmark-gate.json). The additive evaluator
control was added afterward. [Artifact revalidation](receipts/benchmark-artifacts.json)
confirms unchanged compiler executables, Wasm modules, runtime components,
legacy artifacts, benchmark harness inputs and production source hashes. The
same timings were retained without pretending to have measured a new session.

## Limits and next increment

Source traps are instance-fatal: retire the instance. Direct share/shared-open
preflight and explicit enqueue/clean have narrower preservation/resumption
contracts; unwound source-local roots cannot be recovered. Production cleanup
capacity exceeds every chain fitting the fixed heap, but deliberate debug
limits can suspend it. Debug pointers and memory are privileged, not an external
stale-pointer/restore ABI.

Pinned Node arm64 crashes on wide `return_call` frames. Owned emission uses tail
calls only when target live arity and the complete caller frame are each at
most 16 slots; wider source calls use `call` and may exhaust the host stack.
Reclamation itself never recurses through the Wasm stack.

R3 is qualified for sequential immutable Data in the current monomorphic core.
R7 is qualified for bounded resumable sequential cleanup. Closures, generics,
literal boxing, task/device holders, GPU readers, cancellation, mutable/cyclic
graphs and source exception recovery remain outside this profile. Integration
must supply ownership layouts/actions for the concurrent language extensions
and separately qualify task/device lifetime.

Census approval and generated inventories are current. The census has no reviewed
adapter for `compiler-owned-wasm`, so this gate's fixtures do not yet contribute
to its accepted feature evidence. Existing `compiler-io` and `compiler-sugar`
adapter warnings remain. The coordinator should add the owned adapter when
using this suite for census acceptance, refresh shared receipts after merging,
and perform live bounded Perch review before style acceptance.
