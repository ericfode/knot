# Hill-climbing Knot

1. Select a workload, target metric and practical margin before changing the
   compiler. Keep this harness, suite and frozen expectations identical on both
   compiler revisions. Run the independent compiler gates first.
2. Record a baseline, then measure the candidate in its own checkout:

   ```sh
   npm run bench:baseline -- --name=main-20260927
   npm run bench -- --out=.local/bench/results/candidate.json
   npm run bench:compare -- main-20260927 .local/bench/results/candidate.json
   ```

3. Inspect every metric. Exit 0 means no detected regression, not a win; exit 1
   flags a regression; exit 2 refuses insufficient/incompatible evidence. New
   accepted fixture coverage requires a fresh baseline. Do not waive guards or
   prune slow cases to obtain a better verdict.
4. Confirm a proposed improvement in independent sessions, with alternating
   run order and an otherwise idle machine. The seven-sample default is an
   initial screen; use `--repeat=15` or more for decisions. Warm batches share
   process/JIT/GC state, and per-row intervals have no multiple-test correction.

## Actual before/after control on this machine

Two distinct executions on **2026-09-27 PDT** (2026-09-28 **01:59:05–02:01:00**
and **02:01:51–02:04:31 UTC**), using Apple M5 Max / 18 logical CPUs / 128 GiB,
Darwin 25.5.0 arm64, Node 22.22.3, Bun 1.3.14, Apple clang 21 and the installed
MacOSX26.5 SDK. The explicit Xcode toolchain environment is recorded in
[REPORT.md](REPORT.md). No controlled idle-machine condition is claimed.

Commands actually run:

```sh
npm run bench:baseline -- --name=main-20260927
npm run bench -- --out=.local/bench/results/bench-2-after.json
npm run -s bench:compare -- main-20260927 .local/bench/results/bench-2-after.json
```

Both used the unchanged compiler source at `fa31fec064ba0993ed31205fd4b4fdc00df5d761`, with the uncommitted bench-2
harness present (`dirty: true`). Source and harness hash maps match exactly.
This is an A/A noise control for the workflow, not an optimization experiment.
Both runs passed all correctness guards: 31 measured / 170 excluded programs,
seven samples per available metric, and 266 runtime batches each. The shortest
batch in each run was **10.000 ms**.

Selected medians from native-compiler output (fields runtime includes fresh
instances). Ratios are after/before with 95% bootstrap intervals and a 2% margin:

| Case / metric | Before | After | Unit | Ratio [95% CI] | Verdict |
| --- | ---: | ---: | --- | --- | --- |
| peano-192 / runtime | 35243.097 | 49734.375 | ns/call | 1.411 [0.731, 1.994] | no change |
| cells-192 / runtime | 54775.391 | 42148.602 | ns/call | 0.769 [0.186, 1.456] | no change |
| wide-192 / runtime | 32.944 | 29.519 | ns/call | 0.896 [0.371, 1.000] | no change |
| inline-192 / runtime | 1912.141 | 1464.777 | ns/call | 0.766 [0.480, 1.316] | no change |
| cells-192 / compile | 7.424 | 6.037 | ms | 0.813 [0.755, 0.889] | faster |
| wide-192 / evaluate | 15.042 | 16.416 | ms | 1.091 [1.027, 1.193] | slower |

The complete comparison contains **222 target rows: 187 no change, 12 faster,
23 slower**. All 62 size rows are unchanged. **CLI exit 1** correctly retains
the regression verdict. No optimization is accepted: the unchanged-source
control itself exhibits substantial session variation. The next actual compiler
candidate needs fresh repeated controls, not a speedup claim from these rows.

Full evidence: [comparison](receipts/comparison.json),
[before raw result](receipts/hillclimb-before.json.gz),
[after raw result](receipts/hillclimb-after.json.gz). Decompress the raw results
to new JSON files to replay `bench:compare`; every sample and correctness record
is retained. Original JSON SHA-256 values are recorded in the comparison file.
