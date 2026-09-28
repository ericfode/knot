# Device records 2 — gpu-2

Implemented `knot-device-records-2` under D5/D10. **CPU and shader validation
pass; Metal execution is pending coordinator qualification.** This is a new
record runtime, not compiler emission or a GPU performance result. Runtime-1
and the old 38-case probe retain their original contracts and bytes.

The mechanism is one ownership graph: object fields, captures, pending releases
and join results are edges. Type edges move; Data edges count. A single device
writer commits each transition to a separate published buffer. The same generic
shader executes bounded programs with explicit PC, captures, branch/jump,
suspension, and defunctionalized continuation return.

| Fresh gate | Result |
|---|---|
| Complete `PROOF.bend` | 28 filled laws, `All terms check.` |
| Store/scheduler differential | 35 fixtures, 4,464 transitions, 308 complete snapshots, seed Bun = native = independent Python |
| Program driver differential | 7 programs, 29 complete round snapshots, seed Bun = native = independent Python |
| CPU semantic mutants | 6/6 type-correct mutants killed by fixed observations and named laws |
| Host validation/layout | 64 controls pass |
| WGSL validation | 11 variants, 33 pipelines; 10 mutants constructed and typechecked |
| WGSL semantic kills | Unrun: null backend cannot kill a semantic mutant |
| Offline style preflight | 146 declarations; 24 truncated contexts; composition available, 36,810/48,000 bytes; no unresolved references; exit 3 |

The 4,096-slot fill uses a runtime-generated command list: a giant source
literal exceeded the seed's expansion stack. This changes test transport, not
the expected capacity or the command sequence. Large fills sample the first,
exact-full and rejected-full states; every command's status is still compared,
and the Python oracle audits the whole owning graph after every command. The
other fixtures compare complete state after every transition. No elapsed-time
or speed claim is inferred from these runs.

## Device qualification (coordinator, 2026-09-27)

The executor's sandbox had no adapter. The coordinator ran the default device
command on the host's Metal adapter (Apple M5 Max, `metal-3`, not a fallback):
`python3 research/adaptive-tasks/runtime2/check.py --receipt
research/adaptive-tasks/runtime2/receipts/device-metal.json`.

Results:

- **Runtime2 on Metal:** passes. It covers 35 cases and 7 programs over 29
  rounds, with 4,464 commands, 8,986 dispatches and 674 observations. The run
  used 11 shader variants (33 pipelines) and killed **10 of 10** WGSL semantic
  mutants.
- **Runtime-1 on Metal:** still passes. That is 16 cases, with 9 of 9 mutants
  killed.
- **Old 38-case harness:** compares equal to its `185b7d5` baseline.

No speed claim is made.

## Reproduce

```sh
export BEND_NO_TELEMETRY=1
python3 research/adaptive-tasks/runtime2/check.py --cpu-only
python3 research/adaptive-tasks/runtime2/check.py --validate-only
# Coordinator: one command for actual Metal execution and ten semantic kills.
python3 research/adaptive-tasks/runtime2/check.py
# Existing CPU replay, unchanged-file hashes and retained Metal comparison:
python3 research/adaptive-tasks/runtime2/replay.py
# All registered compiler gates, including gpu-2:
npm run -s gates
npm run -s gates:verify
```

Default outputs are ignored `.local/gpu-2/runtime2/`. `--out-dir` selects another
replay destination. `--receipt PATH` explicitly writes a receipt; the registered
CPU gate uses `receipts/cpu.json`. No command rewrites an old probe's receipts.
The coordinator must additionally rerun `runtime/check.py` on Metal and the old
`gpu/check.mjs --compare-receipt runtime/receipts/regression-before-185b7d5.json`
with paths relative to `research/adaptive-tasks/` (or absolute paths). Comparing
retained Metal receipts is historical evidence, not fresh device execution.

`bundle.py FILE.json --adapter-bytes N` validates external bundles, returning
Validated / Invalid / Unsupported / Exhausted / HostFailure with exit codes
0 / 2 / 3 / 4 / 5. Bundles contain `version:2`, `profile:2`, an explicit `config`
matching `layout.json`, and eight-word `instructions`. An optional supplied
layout must exactly match the derived integer layout. Arbitrary initial snapshots
are not admitted. The fixture runner also directly exercises malformed runtime
requests to check that device rejection preserves every owner.

## Interface and limits

See [the full contract](SPEC.md), [layout](layout.json),
[compiler mapping](INTERFACE.md), and [law review](LAW_REVIEW.md).
Storage counts are bounded by checked adapter binding sizes rather than two
records. The gate actually fills 1/2/64/4,096 object slots and tests one more;
layout arithmetic tests all four table counts at those sizes, exact byte limits,
and maximal representable storage ranges without allocating enormous host arrays.

This profile is deliberately serial. It qualifies preallocated capture arrays,
object storage reuse, arbitrary configured object/join arity, and resumable
release. It has one active PC; independent parallel workers, dynamic activation
allocation, source type checking, compiler-generated bundles, source-level
Wasm-to-device differential, Wasm host integration, and performance are later
increments. Scalar payloads are boxed as tags; live fields are object identities.
Object identities are never reused within a bundle, even when storage is reused.
Identity/attempt/count exhaustion is explicit; there is no restore/cross-bundle
identity protocol, mutation/backpatching, cycle collection, or foreign pointer.

Readers use a conservative global barrier. The harness waits for submitted work
before buffer destruction/reuse. General concurrent reader safety and a GPU
memory-model refinement theorem are not established by CPU models or null
validation. A cleanup stack too small for an expansion retains its owner and
reports Exhausted; it does not silently drop work or grow memory.

Compression, Delight, memetic identity, Anticipation and Payoff are all unrated.
Offline preflight is not a style pass. Coordinator work is actual Metal replay,
ten WGSL mutant kills, live semantic/style review with the 24 context blockers
explicit, then source emission into this versioned interface.

Retained receipts: [CPU](receipts/cpu.json), [shader validation](receipts/shader-validation.json),
[replay](receipts/replay.json), [preflight](receipts/preflight.json),
[all registered gates](receipts/GATES.md). Receipt source hashes identify exactly
what was executed; recorded device-unrun status is not replaced by a CPU pass.
