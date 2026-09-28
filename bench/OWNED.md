# Allocation workloads: arena versus owned storage

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-owned-wasm/check.py
BEND_NO_TELEMETRY=1 node bench/owned.mjs --repeat=7
```

This dependency-free runner uses the complete owned gate's verified native/Bun
artifacts. It requires a passed receipt, matches every compiler/gate input hash,
checks each module hash, and reruns the pinned seed and independent evaluator
before timing. It does not reuse binaries from a different source revision.
`--out=PATH` selects a new result path; existing files are never overwritten.
Default results go to ignored `.local/bench/results/`.

[owned.json](owned.json) fixes two allocation-heavy enum-result workloads:
32 structurally recursive consumes and 256 acyclic constructor/consume calls.
Both profiles run the same export with the same result expectation. The complete
recursive `main` is an acceptance control rather than a timing comparison:
it performs 32,768 allocations and the interim arena necessarily exhausts.

Each sample instantiates a fresh module outside the timer, performs eight checked
warmup calls, then times a bounded batch that fits the arena. Every measured
call checks its result. Profiles alternate sample order. Owned live cells,
allocations, peak, pending work and bump are captured outside the timer; each
completed batch must have no live cells or pending releases. Arena memory is
its fixed 65,536-byte reservation; owned memory is the measured 131,072-byte
reservation, including the complete free-list and cleanup regions. Reclamation
reuses those pages and does not shrink them.

Runtime samples include the JS loop, export call and result check; they exclude
module loading, compilation and instantiation. No empty-loop cost is subtracted.
The result contains raw samples, median, unscaled MAD, minimum, module size,
physical counters, machine details and compiler/gate hashes. The existing
benchmark statistics compute owned/arena median ratios and 95% bootstrap
intervals. Repetition within one run is session evidence; background compiler
agents, power, thermal state and JIT changes remain possible noise sources.
No speedup or general performance claim follows from reclamation alone.

## Recorded session

The retained [receipt](../tests/compiler-owned-wasm/receipts/benchmark.json)
passed all correctness guards with seven samples per profile and compiler lane.
Each measured batch performed 4,096 owned allocations and ended at zero live
cells. The full reserved memory was 65,536 bytes for the arena and 131,072 bytes
for owned storage. The owned cell-region high-water mark was 636 bytes for the
recursive workload and 20 bytes for the acyclic allocation workload.

| Workload | Compiler lane | Arena median ns/call | Owned median ns/call | Owned / arena |
| --- | --- | ---: | ---: | ---: |
| Recursive consume | Native | 397.8 | 1,073.6 | 2.70 |
| Recursive consume | Bun | 367.8 | 900.4 | 2.45 |
| Allocation calls | Native | 1,895.9 | 4,697.9 | 2.48 |
| Allocation calls | Bun | 1,841.1 | 4,315.1 | 2.34 |

Both compilers emitted identical bytes and their runtime samples were collected
in separate batches. All four recorded 95% ratio intervals are above one; the
session shows reclamation overhead. Larger warmup campaigns and independent
sessions are needed for optimization decisions. This run occurred alongside
compiler campaign activity and establishes no general throughput result.

The measured session predates the additive deep-call evaluator-limit control.
Its exact [gate receipt](../tests/compiler-owned-wasm/receipts/benchmark-gate.json)
is retained with the original timing provenance. The final gate compares the
compiler and Wasm artifact hashes to that session. The retained
[comparison](../tests/compiler-owned-wasm/receipts/benchmark-artifacts.json)
confirms all eight compiler executables and eight measured Wasm artifacts are
unchanged; no retiming was performed.
