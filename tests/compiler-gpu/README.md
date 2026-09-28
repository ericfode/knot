# Checked core to GPU records — gpu-emit

`src/records.bend` lowers checked `Book` terms into a `knot-device-records-2`
bundle for the unchanged generic WGSL interpreter. It covers Construct, Let,
Case, Application and tail structural self-recursion. Capture intervals are
static; one-shot argument/return joins carry literal issued attempts; recursion
reuses its activation with a back edge. Quantities select move versus share,
and unused owners are released before returning or looping.

The separate profile is `knot-gpu-records-2`. The existing parser, checker,
evaluator, Wasm emitter, driver and public CLIs are unchanged. The manifest,
census and gate registration include the new files. The dependency symlink at
`research/adaptive-tasks/gpu/node_modules` is ignored, not modified or exported.

## Reproduce

```sh
export BEND_NO_TELEMETRY=1
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-gpu/compile.bend \
  -o .local/gpu-emit/compile.js
bun .local/gpu-emit/compile.js tests/compiler-gpu/fixtures/parity.bend \
  .local/gpu-emit/parity.json five
python3 scripts/run-records.py .local/gpu-emit/parity.json --cpu-only --export five
python3 tests/compiler-gpu/check.py --cpu-only
npm run -s gates
npm run -s gates:verify
```

The compiler accepts `[--limits depth bytes] source output entry
[live-ordinals...]`. A bundle embeds one invocation; host `--export` and
`--arguments` are descriptive labels, not runtime inputs. The host prints the
`run-wasm.mjs` JSON shape and optionally writes a complete ownership receipt.
`--quantum`, `--max-rounds`, `--timeout`, `--storage-bytes` and `--receipt` expose
bounded execution. The CPU mode uses the already qualified runtime2 reference;
no host code implements Bend semantics or emission.

**Coordinator device command** (requires the existing WebGPU package and Metal):

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-gpu/check.py --device \
  --receipt tests/compiler-gpu/receipts/device.json
```

This also checks the five emitted compiler mutants on device and compares
complete published state with CPU simulation for all source calls and selected
suspension quanta. It writes a device receipt and compressed device observations.
The executor's attempted device invocation returned `HostFailure records real
Metal adapter unavailable`; CPU evidence does not establish GPU execution.

## Fixed corpus and evidence

`expectations.json` was frozen from the pinned reference before the emitter was
implemented. Existing literal tags and assertions remain fixed.

- Existing fields-Wasm fixtures: pair, nested fields, aliasing/drop and erasure.
- Existing Wasm fixtures: three colors and argument order (including erased args).
- New `parity.bend`: the `even` mechanism from the recursion corpus, with enum
  result entries for 0, 1, 2, 5 and 6 successors.
- New `sharing.bend`: a reusable Data pair, repeated child edges and two opens.
- New `type-loop.bend`: unique Type recursion, accumulator transfer and unused
  tree cleanup on each iteration.
- New rejected fixtures: non-tail `recursive-activation` and repeated-call
  `dynamic-attempt`; the original recursion `direct.bend` supplies the separate
  structured-result rejection.

The new gate compares 53 reference calls over 9 programs with 106 evaluator,
106 actual Wasm and 106 records observations from two compiler builds. All
native/Bun bundles are byte-identical. It checks 12 rejection observations,
25 compiler/host boundaries, 6 suspension controls, 4 one-step replays and
13 filled laws. See [the law review](LAW_REVIEW.md) for the proof boundary.

The five type-correct, transport-valid compiler mutants are wrong branch tag,
move instead of share, missing release, swapped logical join slot, and stale
attempt delivery. Fixed tags, runtime Invalid, or independently checked surviving
owners kill them. Parser/type/host failures and bundle-validator refusals do not
count as semantic kills.

Offline preflight covers 132 declarations in 9 new Bend files with zero provider
requests. It exits 3: 22 declaration contexts truncate (9 caller/byte, 1 file,
12 helper limits); composition has unresolved collaborators/imports and is
48,102 / 48,000 bytes. These are 23 structural blockers. Compression, Delight,
memetic identity, Anticipation and Payoff are unrated. Live review belongs to the
coordinator; no style pass is claimed. `receipts/preflight.json` preserves the
full context limits and identities.

## Limits and next increment

Entry arguments/results are enum-only; all values on device are boxed. Non-tail
self-calls and other calls inside a recursive function remain Unsupported with
specific codes. There is no dynamic activation allocation, dynamic attempt
operand, cancellation lowering, parallelism or performance claim. Static
activation and device capacities are bounded; resource failures are Exhausted.
The thirteen laws cover lowering helpers, not general source/compiler/device
refinement. Actual Wasm recursion evidence is limited to this corpus.

The coordinator must run Metal and live Perch qualification. A subsequent
runtime/interface increment needs dynamic activation and issued-attempt
transport before general recursion can lower safely. More precise path analysis
could admit one-shot helper calls in recursive base arms without that extension.

All 16 registered deterministic gates pass, and `gates:verify` passes 18 tests.
[Exact per-gate counts](receipts/GATES.md), [gate summary](receipts/gates.json),
[new GPU receipt](receipts/gpu.json), and [preflight](receipts/preflight.json)
retain the verification boundary. Shared receipts were left to the coordinator;
only this increment's fresh GPU receipts were copied from the scratch run.
