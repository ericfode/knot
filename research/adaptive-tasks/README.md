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
   compare, mutate, and write receipts. They contain no semantic evaluator.

## Reproduce

From the repository root, with the existing pinned reference archive, Bun,
Python 3, Node, the native C toolchain, and a hardware Metal adapter:

```sh
npm ci --prefix research/adaptive-tasks/gpu
python3 research/adaptive-tasks/check.py
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
evidence. Successful checks rewrite the two receipts above.

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
