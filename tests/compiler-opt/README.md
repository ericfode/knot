# opt-1: checked core optimization

The optional `knot-core-opt-1` pipeline changes checked function bodies and
rechecks every pass. The default compiler, evaluator and Wasm emitter retain
their existing contracts. Inlining binds actuals once, in order, above the
caller and argument level ceilings. Fold reduces known cases and propagates
only unboxed enum values. Dead removes unused erased/reusable lets. The optional
emitter lowers tail self-calls to `return_call`.

Each pass compares its ordered export names, parameter quantities/types and
result types against the input before checking the output bodies. Datatypes
are carried unchanged. The pipeline stops at a fixed point or returns the last
verified round after eight rounds. Depth/output exhaustion stays a distinct
failure. The direct zero-round helper still reports Exhausted because it has
performed no verification; its existing checked law is retained.

The [contract](SPEC.md), [law review](LAW_REVIEW.md) and
[round-2 report](REVIEW-ROUND-2.md) separate local checked equations, differential
execution, resource observations and review limits. Historical round-one
receipts and benchmarks remain evidence of their original inputs. They do not
qualify the repaired implementation.

## Gate and corpus growth

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-opt/check.py
python3 -B tests/compiler-opt/refresh.py
npm run -s gates
npm run -s gates:verify
```

The optimizer gate derives its cases on every run from the enum Wasm, fielded
Wasm and recursion manifests, its own frozen fixtures/observers/regressions,
and the current benchmark generator. No global corpus, generator or law count
is pinned. Every accepted case runs against the seed, both evaluator settings,
both Wasm settings, and each individual pass in native and Bun lanes. All
original unoptimized module hashes remain hard assertions. Source hashes are
audited; source-only changes do not force a new byte baseline. The original
74 programs also retain their observed fixed-point assertions. New programs
record convergence without requiring it for successful optimization.

New corpus entries run the same differentials immediately, even before their
off bytes are frozen. `unfrozen_off_programs` in the receipt lists that gap.
Freeze new off-path hashes explicitly:

1. Add the source and seed/literal expectations to its owning manifest, or add
   a generated benchmark with an independent seed call. Keep prior expectations
   and `baseline.json` unchanged. For a new structured recursion result, append
   a seed-checked complete-tree observer plus a near-miss call to
   `extensions.json.observers`, using the existing observer schema. The gate
   refuses to substitute a pointer observation for the missing Wasm check.
2. Run the gate. Inspect the differential results and the reported unfrozen keys.
3. Produce an independently checked candidate for selected keys:

   ```sh
   python3 tests/compiler-opt/freeze.py --case compiler-wasm-example
   ```

   This rebuilds both off compilers/evaluators, checks seed/evaluator/host values
   and equal native/Bun modules, and writes an ignored candidate receipt. A
   structured case must include its new enum observer in the selection too.
4. Review that candidate, then repeat with `--append`. Only
   `extensions.json.baselines` is extended. Existing baseline entries cannot be
   replaced or shadowed. The next gate run enforces the new hashes. Commit the
   new fixtures, expectations and extension explicitly.

Editing an existing source may change its source identity, but changing its
frozen off bytes still fails. Such a change needs a separate reviewed,
seed-derived amendment; this freeze command cannot bless it. Shared recursion
observers use the current source plus the fixed literal observer suffix when
the original source changes, so stale copies cannot supply a passing result.

The gate records Invalid, Unsupported, Exhausted, HostFailure and InternalFailure
separately. A missing source preserves preexisting output. A harness timeout or
failed mutant compiler build is not a semantic kill. Direct receipts are
canonicalized with the gate runner's normalizer; full canonical IR is compared
before only its hashes and byte lengths are retained. The coordinator still
owns shared receipt refresh after merging.

## Regression and mutation obligations

`regressions.json` was frozen in a separate commit before the round-2 repairs:
`r_4_13`, `r_20_13` and `arena-sharing` add 11 seed/off-evaluator/off-Wasm calls.
The chains must compile and agree even when eight optimization rounds do not
converge. The sharing fixture succeeds close to the 64 KiB arena boundary;
optimized and Fold-only execution must also succeed. Its original failure was
introduced by Fold alone, without requiring dead-let removal. The frozen
`known` ABI contains both `choose` and `main`.

Seven source mutants remain seed-type-correct and are built in native and Bun:
wrong case selection, used-let deletion, captured lexical level, deletion of
all core exports, premature round exhaustion, boxed-literal duplication and
omission of one non-entry Wasm export. The all-export deletion is caught by the
core recheck. The one-export mutant retains the complete functions and a working
`main`; independent `abi()` decoding catches precisely the missing `choose` and
records `abi-kill`. Calling the missing export separately records HostFailure,
which is never relabelled a semantic kill. Round-limit and arena regressions are
recorded as availability/resource-preservation kills, separate from wrong-value
and core-preservation kills.

Eight offline [corpus controls](test_corpus.py) exercise positive/rejection and
generator growth, current-source observers, missing observer rejection,
duplicate keys, append-only freeze selection and frozen-entry collision.

## First benchmark

Both runs used the Apple M5 Max, Node 22.22.3, Bun 1.3.14 and pinned Bend 2.0.29.
Each case/lane has seven compile, runtime and size samples, 100,000 warmup calls
and 1,000,000 calls per runtime sample. Every case/lane checked 7,100,008 results.
The runs were sequential; runtime samples share one Node process per case/lane.
These are same-host sample intervals, not independent-run or cross-host claims.

Ratios below are pipeline **on / off**, with 95% percentile bootstrap intervals.
The comparison uses the existing 2% margin. Bytes are identical across compiler
lanes; their intervals are point intervals because all seven emissions match.

| Case | Compiler lane | Compile ratio [95% CI] | Node runtime ratio [95% CI] | Bytes off → on (ratio) |
| --- | --- | --- | --- | --- |
| calls-16 | native | 1.530 [1.491, 1.665] | 0.234 [0.231, 0.240] | 445 → 1,206 (2.710) |
| calls-16 | Bun | 1.711 [1.635, 1.736] | 0.234 [0.230, 0.238] | 445 → 1,206 (2.710) |
| calls-64 | native | 3.076 [2.819, 3.143] | 0.053 [0.052, 0.054] | 1,598 → 4,960 (3.104) |
| calls-64 | Bun | 2.191 [2.159, 2.254] | 0.053 [0.052, 0.054] | 1,598 → 4,960 (3.104) |
| branch-locals | native | 1.156 [1.014, 1.353] | 0.937 [0.924, 0.975] | 106 → 122 (1.151) |
| branch-locals | Bun | 1.411 [1.384, 1.456] | 0.958 [0.946, 0.972] | 106 → 122 (1.151) |
| known | native | 1.015 [0.879, 1.108] | 0.926 [0.812, 1.003] | 70 → 74 (1.057) |
| known | Bun | 1.283 [1.261, 1.322] | 0.965 [0.950, 0.983] | 70 → 74 (1.057) |

The call chains are faster while every module is larger. Most compile paths
are slower. The native branch-locals compile result and both known-case runtime
results do not meet the comparison's decision margin. Seed compiler builds have
one sample per lane, so no build-time confidence interval is available.
`bench:compare` exits **1** for the measured regressions; speed is not this
increment's acceptance condition.

Raw evidence: [off](receipts/bench-off.json), [on](receipts/bench-on.json), and
[complete comparison](receipts/bench-compare.txt). The selected entries and
source identities are recorded. Omitting `--pipeline` keeps the default compiler.

## Style and limits

[Bounded preflight packets](STYLE-REVIEW.md) keep complete optimizer mechanisms
under the unchanged context caps. Every fixture and wrapper receives separate
preflight. Main's interface context support resolves the old helper/caller
truncations; no frozen observer is split or excluded from declaration review.
Structural readiness supplies no conceptual compression, Delight, memetic,
Anticipation or Payoff rating. The coordinator owns live review.

There is no universal preservation theorem, primitive arithmetic, private
function metadata, reclamation or generalized recursion. Inlining remains
limited to 32-node callees and levels below 4,096. An eight-round result can
need further optimization. Existing enum outputs and all successful near-arena
observations must agree; resource failures are never language rejections.

The next increment can measure compile/size costs and whole-body growth under
the existing benchmark controls, extend domains through the explicit freeze
procedure, and obtain live Perch ratings. Shared gate receipts are refreshed by
the coordinator after integration.

The [2026-09-29 refresh](REFRESH-2026-09-29.md) adds 32 seed-frozen edge programs
without changing earlier observations, laws, controls or mutants. Its separate
checker runs within the registered optimizer gate and compares both compiler
hosts with optimization off, the complete pipeline and each individual pass.
The report records current D21/D24/D26
obligations and coordinator integration work.
