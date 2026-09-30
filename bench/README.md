# Knot benchmarks

Measure the current seed-built compiler and its emitted Wasm, with frozen
correctness guards and noise-aware comparisons. No dependencies, network access,
compiler changes or fixture regeneration are needed. The seed is pinned to Bend
2.0.29 (`574b6d3`); commands use Bun `--no-env-file` and `BEND_NO_TELEMETRY=1`.
Prerequisites are the installed seed/packages, Node 22, Bun 1.3.14 and clang >=14.

```sh
npm run bench:baseline -- --name=main-20260927
npm run bench -- --out=.local/bench/results/candidate.json
npm run bench:compare -- main-20260927 .local/bench/results/candidate.json
npm run bench:verify
```

The default suite is **hillclimb**. Baselines live under
`.local/bench/baselines/NAME.json`; the comparison accepts a name or a JSON path.
Existing evidence is never overwritten. Builds, generated workloads, modules,
worker requests and full raw results stay in ignored `.local/bench/`.
Persisted results and verification receipts use `$ROOT` for the checkout,
`.toolchain` for the seed directory, `$BEND_LIB` for installed packages and
`$NODE` for the Node executable. Execution and worker requests retain real
paths. Gate completion text names the exported tree as `$ROOT`, omitting its
temporary `.local/gates` directory. Samples, run IDs, hashes and diagnostics
are retained. Historical receipts can be normalized with explicit owned paths:

```sh
node bench/normalize-receipts.mjs bench/receipts/hillclimb-before.json.gz
node bench/normalize-receipts.mjs --check bench/receipts/hillclimb-before.json.gz
```

See [HILLCLIMB.md](HILLCLIMB.md) for the procedure and a measured comparison.
The [extension contract](SPEC.md) and [literal expectations](expectations.json)
were fixed before implementing the new workloads.

## Workloads

| Suite | Programs | Selection |
| --- | ---: | --- |
| `hillclimb` | 201 | All six frozen fixture suites plus the 12 new generators |
| `recursion` | 19 | Structural recursion and descent boundaries |
| `fields-wasm` | 8 | Fields, aliasing, erasure, arena and deep call fixtures |
| `closures` | 42 | Frozen closures/higher-order corpus |
| `baseslice` | 40 | Frozen reachable Base corpus |
| `generics` | 40 | Frozen generic/quantity corpus |
| `literals` | 40 | Frozen literal/primitive corpus |
| `runtime` | 12 | Peano, fielded lists, wide matches, many small functions |
| `smoke` / `core` / `scaling` | 1 / 9 / 9 | Retained first-wave enum suites |

Every fixture is probed in native and Bun compiler lanes on every run; support
is never inferred from a hardcoded list of today's accepted programs. The same
suite starts timing a newly supported fixture without editing its benchmark.
One frozen enum-signature observation per program is selected (`main` first,
otherwise the first recorded call). This is representative timing, not exhaustive
conformance. The independent compiler gates retain all their original assertions.

Rejected probes remain in the result as `not-yet-compilable`, with exact process
records and distinct **Invalid, Unsupported, Exhausted, HostFailure and
InternalFailure** classifications. Host/internal failures invalidate a run.
Seed-valid programs reported Invalid are explicitly marked **D4 discrepancies**;
they are not benchmark passes for those capabilities. Acceptance of a frozen
seed-negative program invalidates the run. A successful inventory may have zero
measured cases; it cannot establish a performance comparison.

Recursion fixtures return structured trees, outside today's enum-only host ABI.
They receive compiler and evaluator timings and an explicit
`Unsupported / host / structured-result` runtime entry. Raw cell addresses are
never treated as constructor ordinals. The generated recursion/list workloads
return enum observations and exercise the fields Wasm runtime directly. Those
observations do not promote the general recursive Wasm contract to qualified.

`node bench/generate.mjs --runtime` writes deterministic programs at sizes
32, 96 and 192. Peano parity traverses size+1 successors; list traversal consumes
size fielded cells, constructed in 32-cell chunks to respect parser depth;
wide enum matches rotate the penultimate tag to the last; small-function chains
apply size flips. Literal results are checked against the live pinned seed,
both evaluator lanes, and every emitted runtime call. The original
`node bench/generate.mjs` still produces the nine scaling cases.

## Measurements and guards

| Metric | Unit | Timed work |
| --- | --- | --- |
| Compiler build | ms | Seed to native/JS compiler, including native C compilation; informational |
| Compile | ms | Fresh CLI process: reading, lexing, parsing, checking, emitting and writing |
| Evaluate | ms | Fresh CLI process: reading, lexing, parsing, checking, evaluating and describing |
| Runtime | ns/call | Warm Node batches; JS loop/result guard and the declared instance lifecycle |
| Output size | bytes | Complete emitted module |

The current driver exposes no phase clocks. `protocol.selfCost` records this
reason and the phases included in each whole-run timer. We do not alter its
output or subtract separate process times to invent lex/parse/check/emit costs.
Every new accepted case gets a compiler total and, when evaluation succeeds, an
evaluator total. Evaluation exhaustion/unsupported outcomes remain explicit;
for example, the deep-call fixture raises compiler parser budgets but the
public evaluator has fixed input limits. Its runtime still has a frozen seed
oracle. Largest accepted inputs can be selected by recorded source hash/path,
family and size; all sizes retain separate rows.

Both `knot-enum-1` and `knot-fields-wasm-1` use the existing checked Bend drivers.
Every compiler invocation requires a fresh file and exact `Built` record.
Artifacts must validate, have no imports, agree byte-for-byte across repeated
compilations in each lane, and satisfy the frozen result. The two lanes must
agree on compilation and evaluation classifications. All generated cases get a
live seed cross-check before timing; fixture oracles retain frozen manifest and
source hashes. Input, compiler, harness and Git identities are rechecked at end.

Enum runtime calls reuse one instance. Fields-profile calls create a fresh
instance **for each call**, because the private 64 KiB arena has no reset or
reclamation. The fields measurement includes instantiation and allocation/GC
cost, reported as `fresh-instance-per-call`; it is not pure Wasm instruction
latency. Both lanes compile the Wasm module once outside the timer, warm up, and
iterate inside one Node process. Every call, including validation and warmup,
checks its result. Stack and arena exhaustion are distinct from other host traps.

One runtime **iteration/sample is a batch**, not a single source invocation.
New suites have seven samples by default. Each batch executes at least 64 calls
and continues in 64-call chunks until at least **10 ms** have elapsed. Raw
`batches` retain actual calls and nanoseconds; ns/call is their quotient. Short
work is accumulated, never discarded or extrapolated. Warmup defaults to 32
calls. The retained enum suites keep their original fixed-count settings.

`--suite=NAME`, `--repeat=N`, `--warmup=N`, `--iterations=N`, `--build-repeat=N`
and `--out=FILE` are available. Iterations is the minimum/chunk call count in new
suites. Repeats override every case; build-repeat defaults to one. All counts
must be positive. Builds and measurements are sequential; each subprocess has
a 120-second timeout. A mismatch, changing input, missing artifact or host/internal
failure makes the result unusable, with the failure record retained. Arena/stack
exhaustion is runtime-unavailable with no timing samples; the intentional
`arena-overflow` fixture exercises this path even with fresh instances.

## Comparison and verification

Raw samples retain count, median, unscaled MAD and minimum. Comparison recomputes
summaries, uses a deterministic independent-sample percentile bootstrap (10,000
resamples, 95% interval), and requires the entire candidate/baseline ratio
interval to cross the 2% practical margin. Smaller is better. No blended score,
outlier removal, or multiple-comparison correction is applied. At least three
samples on each side are required. `no change` is inconclusive, not equivalence.

Exit 0 means no significant target regression; 1 means a regression; 2 means
incompatible, failed, malformed or insufficient evidence. Compiler/evaluator
latency, runtime and size are separate targets. Builds are informational unless
`--include-build` is supplied. `--margin`, `--confidence`, `--resamples` and
`--seed` adjust the comparison. Changed machine/tools, harness, workload sources,
oracles, profile, budgets, coverage or timing protocol require a fresh baseline.
Compiler source and revision may differ. Repetition counts may differ.

`bench:verify` retains the original unit tests and two-lane enum smoke, adds
manifest/classification/lifecycle/batch tests, then runs the complete hillclimb
inventory at one sample. Four seed-type-correct semantic mutants (wrong parity
base, ignored cell, wrong match arm and omitted flip) must compile in both lanes
and be killed by unchanged runtime expectations. Its own tracked receipt is
[receipts/verification.json](receipts/verification.json). It also checks
[24 seed-frozen edge programs](fixtures/refresh/CONTRACT.md) in both lanes,
including empty/singleton inputs, odd/even lengths and enum wraparound. These
controls remain outside the timed inventory; their evaluator and Wasm results
and byte-identical lane pairs are in [refresh-edges.json](receipts/refresh-edges.json).
The [refresh report](REFRESH.md) records the current decisions, exact gate counts
and coordinator integration work. The compiler gate runner
is deliberately unchanged under bench-2's ownership instruction; the coordinator
must register this command if it should run through `npm run gates`.

Offline style preflight covers each generated Bend program separately. Its
receipts are under `bench/receipts/preflight/`; no laws or production Bend files
were added. Preflight is structural evidence only; live semantic/style review
and qualification remain the coordinator's responsibility.

## Historical first-wave measurement (f324221)

The following example belongs to the original fixed-count enum harness. It is
retained as historical evidence; version 2 needs fresh baselines.


Actual runs on **2026-09-27**, core at 23:17:00–23:17:09 UTC and scaling at
23:17:24–23:17:55 UTC. Machine fingerprint: **Apple M5 Max, 18 logical CPUs,
128 GiB RAM, macOS/Darwin 25.5.0 arm64; Node v22.22.3; Bun 1.3.14; Apple clang
21.0.0; Bend 2.0.29**, declared pin
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. Compiler source commit:
`f2ae8bae35e0a800201e479342fac96d69478168`; dirty flag **true** because this
benchmark increment was present before its commit. No compiler source changed.

Commands actually run:

```sh
npm run bench:verify
npm run bench:baseline -- --suite=core --repeat=7 --name=bench-1-core
npm run bench -- --suite=scaling --repeat=7 --out=.local/bench/results/bench-1-scaling.json
npm run bench:compare -- .local/bench/baselines/bench-1-core.json .local/bench/baselines/bench-1-core.json
```

All 35 compiler-free tests and the real two-lane smoke passed. Both larger suites
passed all correctness guards. Each larger-suite case used 7 compile samples,
100,000 warmup calls and 7 batches of 1,000,000 measured calls. Selected **medians**:

| Case | Native compile ms | Bun compile ms | Node ns/call, native output | Node ns/call, Bun output | Wasm bytes, both |
| --- | ---: | ---: | ---: | ---: | ---: |
| core: flag-flip | 2.166 | 22.222 | 6.051 | 6.009 | 68 |
| scaling: enum-16 | 1.950 | 21.173 | 5.977 | 5.989 | 42 |
| scaling: enum-128 | 3.249 | 27.726 | 6.149 | 6.110 | 42 |
| scaling: match-16 | 2.172 | 23.983 | 6.142 | 6.160 | 207 |
| scaling: match-64 | 3.538 | 31.332 | 10.662 | 10.753 | 735 |
| scaling: match-128 | 6.702 | 43.921 | 17.174 | 16.998 | 1566 |
| scaling: calls-16 | 2.333 | 25.314 | 38.863 | 40.096 | 445 |
| scaling: calls-64 | 3.921 | 34.966 | 367.498 | 366.218 | 1598 |
| scaling: calls-128 | 7.190 | 48.316 | 778.960 | 780.381 | 3173 |

For `calls-128`, native compile MAD/min were **0.067/6.831 ms** and Bun compile
MAD/min **0.500/47.449 ms**. Runtime MAD/min were **1.399/751.589 ns** for native
output and **0.793/779.279 ns** for Bun output. Scaling compiler builds took
**4935.581 ms native** and **164.463 ms Bun**, each one observation, with no
build confidence claim. Evaluator setup costs are separate in the result.

The same-file CLI comparison returned exit 0, ratio 1.0 for every row and no
significant change. This checks the comparison path; these runs contain no
optimization candidate and establish no speedup.

Targeted Perch review of `bench/lib/compare.mjs::compareResults` was unavailable:
the initial parser cache lock was outside the writable sandbox; an isolated
local cache resolved that, then the provider reported no exported API key.
The wrapper was called with a copied environment to disable dotenv loading;
no credential file was read and the missing-key request was not retried.
This is not a semantic-review pass. No compiler Bend declaration or law changed.

Raw local evidence is in `.local/bench/baselines/bench-1-core.json` and
`.local/bench/results/bench-1-scaling.json`. Full per-file hashes and samples are
in those ignored results. Reproducibility identifiers (SHA-256):

- Core result: `c9ad27a70ef623681c5c31f2a7f9626b159a7c582127ec5bad182c8f3ed13957`.
- Scaling result: `aadfa6c03887000c71f3216d38e899a74bfd762fd49f2628e29ab64a067f4ee1`.
- Ordered JSON source-hash map: `168e77fa452387ac9e0027f974fd1b2b4f99d73d8848f657b93c4c1ee1c0ee7f`.
- Ordered JSON harness-hash map: `1001ce36bb3759d1e723e59259bc5facd231283e76e2e61cdf23d8f47eb3569c`.
- Installed seed source digest: `9a13271d23953046a77859d0e993e2c99423afd28899c403c09cddd5dad9e5dd`.
