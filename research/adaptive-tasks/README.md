# Adaptive continuation tasks: first executable probe

Implemented and checked on 2026-09-26. A Bend ownership/checkpoint protocol and
a handwritten WGSL machine now run against an independent Bend evaluator on a
real Apple M5 Max through Dawn's Metal backend. This establishes feasibility
for a bounded tree language. Knot does not yet compile Bend to Wasm or WGSL.

## Verified increment

| Evidence | Result | Boundary |
|---|---|---|
| Bend equations | 12 checked laws, including `run(m,run(n,r)) = run(n+m,r)` for arbitrary Nat budgets and complete affine states | No whole-program CPU/device simulation theorem |
| Ownership | Valid move control checks; task reuse and double slot extraction fail with `consumed more than once` | Affinity permits dropping; external-resource cleanup is not modeled |
| CPU execution | Ten independent source-tree fixtures and eleven protocol observations agree on upstream JS/native paths | Uses the upstream seed; no Knot emitter |
| Semantic mutations | Five type-valid Bend mutations fail named laws and observations; three valid WGSL pipelines fail the Bend result oracle | Finite falsification evidence |
| Actual device | 38 runs, 1,713 dispatches; ordered results, saved captures, multiple quanta, explicit resource failures, repeated release/recreation | One Metal adapter; native Node host, not a Wasm/browser host |
| Perch | Eight files × six Bend rules; bounded law packet × eight rules; real provider responses | Advisory review; WGSL/Python/JavaScript are outside these rules |

The [full check receipt](receipts/checks.json) records exact source/toolchain
hashes, proof diagnostics, negative controls, native execution, and mutations.
The [device receipt](receipts/gpu.json) records adapter identity and every run.
The combined [research Perch report](../PERCH_REPORT.md) includes the older join
model and exact reviewed hashes. Match hashes before treating a receipt as
evidence for edited source.

The [generated-code walkthrough](codegen/README.md) retains actual upstream
C/JavaScript output and the GPU packer's output for the `cpu_frames` fixture,
with commands and a separate execution receipt. Its Whiteboard excerpts link
each artifact back to the code that produces it.

## Read the implementation

1. [SPEC.md](SPEC.md) defines the scope and observable contract.
2. [slot.bend](slot.bend) transfers affine payloads into/out of a slot. Rejected
   insertion returns both the original slot and the uninserted payload.
3. [task.bend](task.bend) defines owned frames, logical destinations, residual
   work, bounded execution, and repeated slices. Zero fuel preserves full state.
4. [LAWS.bend](LAWS.bend) and [PROOF.bend](PROOF.bend) specify and prove those
   contracts; [LAW_REVIEW.md](LAW_REVIEW.md) records coverage and proof limits.
5. [oracle.bend](oracle.bend) evaluates source trees recursively, independently
   of scheduling. [fixtures.bend](fixtures.bend) supplies values to the device
   runner; [conformance.bend](conformance.bend) exercises the Bend protocol.
6. [gpu/tasks.wgsl](gpu/tasks.wgsl) implements three dispatch phases. Its
   [layout and lifetime contract](DEVICE-PROTOCOL.md) explains their invariants.
7. [check.py](check.py) and [gpu/check.mjs](gpu/check.mjs) build, dispatch,
   compare, mutate, and write replay evidence. They contain no semantic evaluator.

## Reproduce

From the repository root, with the existing pinned reference archive, Bun,
Python 3, Node, the native C toolchain, and a hardware Metal adapter:

```sh
npm ci --prefix research/adaptive-tasks/gpu
BEND_NO_TELEMETRY=1 python3 research/adaptive-tasks/check.py
```

The nested lockfile pins `webgpu` 0.6.1, Dawn's
[Node WebGPU binding](https://github.com/dawn-gpu/node-webgpu). The runner selects
Metal explicitly and rejects a fallback adapter. Dependency installation needs
network access; the check itself uses local inputs. An unavailable device fails
the check. It never counts a CPU fallback as hardware success.

The reference core hashes are pinned by the sibling join experiment to upstream
`574b6d39a235b539eb19a5c532993a0abb3d11ad` (Bend 2.0.29). This does not choose
Knot's compatibility pin or independently verify the seed, Base, or native tools.
Each command has a bounded timeout; a failed run leaves any old receipts as old
evidence. Plain checks write under ignored `.local/adaptive-tasks/replay/` and
never replace the two retained receipts above. `--out-dir DIR` selects another
evidence directory. Only explicit `--update-receipts` replaces retained receipts.

To compare a fresh hardware replay with the retained 38-case run:

```sh
BEND_NO_TELEMETRY=1 python3 research/adaptive-tasks/check.py \
  --out-dir .local/adaptive-tasks/after \
  --compare-receipt research/adaptive-tasks/receipts/gpu.json
```

The standalone GPU runner accepts the same output and comparison flags. The
comparison requires the same ordered case inventory, options, fixture identity,
results, ownership/bounds observations and deterministic transition counters.
It excludes `stateSha256` and `logicalWorkerMoves`: frontier allocation order can
change physical state bytes and logical worker placement. All original live
assertions remain active, including movement in adaptive mode and no movement in
fixed mode. Dates, tool/runner provenance and adapter descriptions are retained
as metadata; both compared receipts must still identify nonfallback Metal runs.
Version 2 receipts include `maxRounds`. The original 38-case receipt is normalized
using its fixed schedule: case 35 has budget 3, case 36 budget 2, all others 512
(zero-based indices).

The offline replay checks preserve all seven retained receipt/generated files:

```sh
node --test research/adaptive-tasks/tests/replay.mjs
BEND_NO_TELEMETRY=1 python3 research/adaptive-tasks/tests/replay.py
BEND_NO_TELEMETRY=1 python3 research/adaptive-tasks/check.py --cpu-only
```

`--cpu-only` runs the existing proof, quantity, native/reference and CPU mutant
gates, recording `cpu-only` rather than device acceptance. It cannot be combined
with `--update-receipts`. The default complete gate still fails when no hardware
adapter is available; completed CPU evidence is saved in `checks.failed.json`
with `HostFailure` for that condition.

## Runtime follow-up

The [R4/R6 record-interpreter increment](runtime/README.md) adds generation-checked
slot reuse, bounded frontier ownership, an independent Bend three-phase model,
mutants and a versioned layout candidate. Its CPU and shader-validation gates pass;
real-device qualification is blocked by unavailable Metal access in the executor.
It does not replace or promote the historical 38-case device receipt.

## What this teaches us

Source order can be preserved while ready work changes frontier position and
logical worker. Saved captures and destinations survive suspension. A bounded
dispatch protocol can avoid cross-workgroup spin waiting and detect capacity
failure before writing beyond the declared frontier. The observed movement is
between **logical dispatch lanes**, not measured physical GPU cores.

This probe eagerly preallocates the entire tree and never reuses task slots.
Its host reads all state after every round for assertions. It therefore does
not establish useful speed, efficient memory use, a production scheduling
policy, general closure storage, or portability. Fixed placement is a semantic
control here; no timing comparison or performance winner is claimed.

Next, refine the owning slot and ordered-join contracts into a bounded indexed
arena/frontier with explicit handle lifetimes. Keep this executable oracle while
introducing a compiler-emitted representation. Wasm host execution, a Bend
source-to-device case, sharing, cancellation, and general allocation each still
need their own gates; none is implied by these results.
