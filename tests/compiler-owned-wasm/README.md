# Owned Wasm: source and runtime gate

The `knot-owned-wasm-1` emitter reclaims unique Type cells and reference-counted
immutable Data cells through size-class free lists and an explicit release
stack. [SPEC.md](SPEC.md) states the payload, debug and failure contracts.
This is a bounded sequential runtime; GPU readers and suspended task roots
remain separate work.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-owned-wasm/check.py
BEND_NO_TELEMETRY=1 node bench/owned.mjs --repeat=7
```

The compiler, evaluator and runtime probe each build with the pinned seed on
native and Bun. The host validates modules and decodes only reviewed physical
layouts. Source results come from literal expectations and the seed; no host
code implements the language, checker or emitter. The complete gate writes
[receipts/owned-wasm.json](receipts/owned-wasm.json). Build outputs remain under
`.local/compiler-owned-wasm/`.

The initial D7 freeze is [expectations.json](expectations.json), binding
[cases.json](cases.json), source fixtures and the legacy byte baseline before
owned emission. Its [first seed replay](receipts/reference.json) contains 63
observations. Later independent coverage is additive: [review-cases.json](review-cases.json)
adds shared boxed children; [boundaries.json](boundaries.json) fixes reserved
export rejection; [exhaustion-cases.json](exhaustion-cases.json) fixes a source
heap-exhaustion control; [evaluator-extensions.json](evaluator-extensions.json)
fixes the deep-call evaluator value under its existing larger compile limits.
Existing expectations are unchanged.

The gate covers every fields-Wasm and recursion corpus program, the four
source controls from the data-lifetime packet, and focused lifetime fixtures:

- `unused-owned`: unused nested Type/Data graph cleanup.
- `branch-cleanup`: a reusable Data binding used in only one branch.
- `share-live`: a retained Data value survives an intervening allocation.
- `recursive-reuse`: 32,768 lifetime allocations in one entry; the arena
  exhausts, while owned execution completes in bounded memory.
- `release-chain`: 65 cells suspended at zero/one cleanup work, blocked by a
  one-frame stack limit, then completely reclaimed after the limit increases.
- `shared-boxed`: opening a shared parent with duplicate boxed edges preserves
  one physical leaf with three incoming references.

Each returned graph must have exactly the runtime's live-cell count and the
expected Data incoming counts. Every enum return has zero live cells. Structured
results are released after inspection and must leave no pending work. Two
persistent workloads check reuse across calls in one instance. Legacy Fields
and Enum modules are compared byte-for-byte against the pre-owned baseline.

[model.bend](model.bend) is an independent allocator model. Its 12 complete
states are compared to Wasm memory by [runtime-check.mjs](runtime-check.mjs),
which also checks ten direct runtime obligations, including duplicate-edge
shared-open overflow without mutation and the maximum cell-region chain.
The complete heap, ownership and independent model proof entries check 43 filled laws. Their
algebraic/model/emission claims are narrower than a general Wasm ownership
refinement theorem.

[mutants.json](mutants.json) names five unique, type-correct replacements:
missing release, double release, omitted sharing, premature shared-cell reuse,
and an off-by-one release-stack bound. Each must fail its unchanged independent
observation in both compiler lanes, after seed typecheck and Wasm validation.
The historical [wide-tail attempt](receipts/attempt-wide-tail.json) records the
pinned Node Liftoff crash that required an emitter fallback. It is a host failure,
not a semantic mutant kill or evidence of successful execution.

The existing deep-call evaluator retains its default parser-budget Exhausted
outcome. [eval-deep-call.bend](eval-deep-call.bend) loads the unchanged fixture
with the frozen compile input limits and invokes the unchanged evaluator.
Its two added native/Bun observations return `Evaluated\t0\t1\tOn{}`. All 56
positive source calls therefore have evaluator values agreeing with the seed
and owned Wasm through the ordinary or extended controls. Source-level runtime exhaustion
is instance-fatal because source-local owners are no longer externally reachable.
Only the direct cleanup protocol promises resumability. Debug exports are
privileged; arbitrary host pointers, source recovery, cycles, closures and
concurrent readers are not qualified here.

The [allocation benchmark](../../bench/OWNED.md) compares the same checked
workloads against the arena profile with explicit correctness guards and full
reserved-memory accounting. Offline style preflight is structural evidence;
live Perch ratings remain the coordinator's task.

## Verified increment

The complete owned gate passed on 2026-09-28 UTC (2026-09-27 local).

| Observation | Passed count |
| --- | ---: |
| Positive programs / fixed calls | 29 / 56 |
| Main seed observations, including classification controls | 64 |
| Main evaluator observations, including two expected parser-budget exhaustions | 112 |
| Added evaluator value agreements at the fixed larger input limits | 2 |
| Owned Wasm value/accounting observations | 112 |
| Native/Bun owned module byte agreements | 29 |
| Frozen legacy byte checks | 116 |
| Invalid/Unsupported compiler/evaluator pairs | 16 |
| Boundary probes | 24 |
| Independent allocator state comparisons | 24 |
| Direct runtime witnesses | 20 |
| Checked laws | 43 |
| Type-correct semantic mutants / lane kills | 5 / 10 |

The [proof-placement comparison](receipts/proof-split-artifacts.json) preserves
all 176 artifact hashes across the proof split: 58 owned modules, two runtime
component byte transcripts and 116 legacy artifacts. All 43 laws pass through
the three complete proof entry points.

The boundary probes additionally rerun four seed and four evaluator calls.
Each lane's persistent control completes 20,000 allocations with peak one cell.
The recursive control completes four calls, 131,072 allocations, peak 32 cells,
and no live cells or pending work on return. Its cell-region high-water mark is
636 bytes; its complete physical reservation remains 131,072 bytes. The arena
control reports Exhausted on one full recursive entry call.

The missing-release mutant leaves five cells live after an enum return. The
double-release mutant triggers the runtime's InternalFailure check. Omitted
sharing and premature reuse both return `Pair{Value{On{}},Value{On{}}}` instead
of the fixed `Pair{Value{On{}},Value{Off{}}}`, with incorrect incoming counts.
The stack-bound mutant admits two pending frames under the one-frame limit.
These observations kill each mutant in both lanes.

[receipts/benchmark.json](receipts/benchmark.json) retains seven timing samples
per workload/profile/compiler lane. Median owned costs are 2.34–2.70 times the
arena cost in this session. Reclamation has a measured cost and permits the
long workload that exhausts the arena; these are separate results.

The benchmark timing session predates the additive evaluator control. Its
[matching gate receipt](receipts/benchmark-gate.json) is retained unchanged;
the [artifact comparison](receipts/benchmark-artifacts.json) confirms all eight
compiler executables and all eight measured Wasm artifacts are unchanged.
