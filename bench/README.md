# Knot benchmarks

A dependency-free framework for measuring today's seed-built enum compiler and
future optimization passes. It does not establish full self-hosting or GPU
performance. The benchmark driver and statistics use Node's standard library.

## Run

Prerequisites: Node 22, Bun 1.3.14, clang >= 14, and the existing pinned seed at
`.toolchain/bend-2.0.29-574b6d3`, including its already available imports. No
additional npm dependencies are required by the harness. Native/Bun builds use
`src/compile-cli.bend -o OUTPUT`, as in
[the Wasm gate](../tests/compiler-wasm/README.md). The seed is invoked directly
with `bun --no-env-file` and `BEND_NO_TELEMETRY=1`. It uses `CC` if set, otherwise
`clang`. Build dependencies must be provisioned before a timed run.

```sh
npm run bench -- --suite=smoke
npm run bench -- --suite=core --repeat=15 --out=.local/bench/results/core.json
npm run bench -- --suite=scaling --repeat=15
npm run bench:baseline -- --suite=scaling --repeat=15 --name=main-before-pass
npm run bench:compare -- .local/bench/baselines/main-before-pass.json .local/bench/results/candidate.json
npm run bench:verify
```

`bench` defaults to `core`. `--repeat=N` overrides every case's repetition count;
otherwise each case supplies it. `--warmup=N` and `--iterations=N` override the
suite's runtime settings. `--build-repeat=N` repeats seed builds (default 1).
All counts must be positive integers. `--help` lists the options.

Without `--out`, results have unique timestamped names under
`.local/bench/results/`. `bench:baseline` uses `.local/bench/baselines/`; `--name`
sets its name, otherwise the suite and timestamp name it. Existing files are
never overwritten. The commands print the absolute result path. Generated
sources, binaries, Wasm, worker requests and raw results stay in ignored
`.local/bench/`. They can be removed after preserving any evidence needed for a
comparison. `bench:verify` runs compiler-free tests followed by the real smoke
suite in both lanes; it does not change `lint:verify` or existing test receipts.

## Suites and correctness

| Suite | Cases | Purpose |
| --- | ---: | --- |
| `smoke` | 1 | `flag.flip(0)`, three repetitions, complete native/Bun path |
| `core` | 9 | Existing enum, nested match, erasure, call, local and ordinal fixtures |
| `scaling` | 9 | Constructor counts, match widths and call depths of 16, 64 and 128 |

Each `bench/suites/*.json` has `schemaVersion`, `name`, `runtime` settings and a
`cases` list. Each case specifies a unique `name`, repository-relative `program`,
export `entry`, live ordinal `args`, and `repeat`. Erased arguments are omitted.
Add cases and suites as the compiler's accepted profile grows; compare only
runs of the same suite and inputs.

Existing fixture calls take their literal expected results directly from
`tests/compiler-wasm/cases.json`. Other calls use `src/eval-cli.bend`, built in
both native and Bun lanes, outside measured compiler/runtime work. Both
evaluators must return the same nullary enum. Generated cases additionally
check the evaluator against a simple closed-form expectation.

`node bench/generate.mjs` deterministically writes the scaling programs under
`.local/bench/generated/`; running `scaling` invokes it automatically. Enums
export identity, match tables rotate to the next constructor, and call chains
apply an even number of flips. These are acyclic programs within today's
resource budgets. The generated sources are workload data, not modifications
to the compiler, packages or accepted laws.

Every timed seed build is exercised with the existing flag literal guard.
Every compiler invocation must return an exact `Built` receipt for a fresh
output file. Each resulting module is validated, instantiated, checked for
imports and live arity, and called against its expected result. Repeated
compilations in a lane must produce identical bytes. Runtime warmup and **every
measured call** also check their results. A mismatch, trap, exhaustion, timeout,
missing artifact or input change invalidates the entire run and produces a
failed result with a nonzero exit. Each subprocess has a 120-second timeout.
Partial/failed records cannot be compared.

These checks cover the listed observations. They do not replace the compiler's
independent proof, negative-fixture, mutation and backend gates, or establish
correctness for inputs absent from the suite. In particular, evaluation shares
the compiler's frontend and is not an independent frontend implementation.

## What the timers mean

| Metric | Unit | Timed work | Default comparison target |
| --- | --- | --- | --- |
| Compiler build | ms | Pinned seed to `compile-cli`, including native C compilation or JS emission | Informational |
| Compile | ms | One fresh native/Bun compiler process, reading source and writing Wasm | Yes |
| Runtime | ns/call | Warmed Node calls to an emitted export, including JS call/loop/result-check overhead | Yes |
| Output size | bytes | Full emitted Wasm file, including all exported functions | Yes |

Builds and measurements are sequential. Each run rebuilds the compilers; it
never reuses a binary from another source revision. Evaluator build/evaluation
costs are recorded separately under `evaluatorBuilds` and the case's oracle.
Every compiler process includes startup, filesystem work and, for Bun, its
startup/JIT cost. One unmeasured compile invocation precedes each case/lane's
samples; its artifact is checked too. This is warm-cache CLI latency, not an
isolated frontend/emitter timer or cold-disk experiment.

For each case/lane a single Node worker validates every emitted artifact, then
uses the last identical module for warmup and all runtime batches. File reading,
Wasm compilation/instantiation and Node process startup are outside its timers.
The worker does not subtract an empty loop or claim to measure pure Wasm
instruction cost. Tiny entries are dominated by the host call and check. Fixed
arguments may favor JIT optimization. Each lane retains its own runtime and
size observations even when both emit identical bytes.

A schema-versioned result retains raw samples plus `n`, median, **unscaled**
median absolute deviation (MAD), and min for every metric. `compilations` keeps
the command, duration, bytes, output hash and checked result for each invocation.
`environment` records CPU model/count, OS/version/architecture/memory, Node,
Bun, clang, seed version and source digest, declared seed revision, Git commit,
dirty flag, `src/*.bend` hashes, and benchmark implementation hashes. The seed
revision is the contract's pin; its source digest fingerprints the installed
copy, which need not contain a Git directory. No environment-variable dump or
credential file is read or recorded.

## Compare

`bench:compare BASE.json NEW.json` reports each case, lane and metric separately.
The ratio is **candidate median / baseline median**: below 1 is faster (or
smaller for bytes). There is no blended score. Summary fields are recomputed
from raw samples when comparing.

The deterministic, independent-sample percentile bootstrap resamples each side
with replacement, calculates the ratio of medians, and takes the central 95%
interval (10,000 resamples by default). A timing is `faster` only if the whole
interval is below `1 - margin`; it is `slower` only if the whole interval is above
`1 + margin`. Size uses `smaller`/`larger`. The default margin is 0.02 (2%).
`no change` means the data do not establish a change beyond that margin; it is
not evidence of equivalence. Minimum sample count is three on each side;
smaller sets say `insufficient samples`, without a confidence interval.

```sh
npm run bench:compare -- BASE.json NEW.json --margin=0.03 --confidence=0.99 --resamples=20000 --seed=17
# Build comparisons need repeated builds in both input runs:
npm run bench:compare -- BASE.json NEW.json --include-build
```

Exit 0 means no significant target regression; it does **not** promise a win.
Exit 1 means at least one target regressed. Exit 2 means failed/malformed or
incompatible evidence, or insufficient target samples. Build intervals are
informational unless `--include-build` is used. An increased code size can fail
the default comparison even when latency improves: inspect the separate rows
and explicitly justify any such tradeoff outside the automatic gate.

Comparisons require matching CPU/OS/tool fingerprints, benchmark code, suite,
program hashes, entries/arguments, expected results and timing settings.
Compiler source hashes and Git revisions may differ: those identify the
candidate. Repetition counts may differ. No option silently overrides these
compatibility checks; changing a benchmark requires a fresh baseline with the
same harness on both revisions.

## Hill-climbing an optimization pass

1. Choose the suite, specific target metric, practical margin and independent
   compiler acceptance gates before changing the compiler. Keep fixtures and
   literal expectations fixed.
2. In the coordinator's existing `main` checkout, with this same benchmark
   version available, record `npm run bench:baseline -- --suite=scaling
   --repeat=15 --name=main-BEFORE`. Record the result's absolute path and source
   commit. Use an otherwise idle machine on power with stable thermal conditions.
3. In the optimization branch's own checkout, run the independent deterministic
   compiler gates, then `npm run bench -- --suite=scaling --repeat=15
   --out=.local/bench/results/candidate.json` with matching settings.
4. Compare the absolute baseline/candidate paths. Accept only with correctness,
   a significant win in the preselected target, and no unexplained significant
   regression in the other rows. A faster build alone is not the default goal.
5. Repeat promising results in separate sessions, alternating baseline and
   candidate run order. Confirm on held-out programs, then retain the accepted
   commit, raw results and comparison settings as the next baseline. The CLI
   records evidence; it does not switch branches, merge or accept changes.

Noise is not removed from samples. Background agents/builds, scheduler placement
on heterogeneous cores, power policy, filesystem caching, temperature, Bun/Node
JIT tiering and GC can dominate small effects. Warm batches within one process
are correlated, so their bootstrap intervals describe the observed session,
not all future machines or runs. A 3-sample smoke suite is a wiring check; use
more samples and independent runs for decisions. Per-row intervals have no
multiple-comparison correction. Preselect a target and confirm it on fresh
runs instead of selecting whichever of many rows happens to win. Seed builds
include cache/dependency effects and default to just one observation.

## Measured example

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
