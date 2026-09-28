# C backend benchmark lane

`node bench/c-run.mjs` measures the corpus in
[`tests/compiler-c/cases.json`](../tests/compiler-c/cases.json), including every
enum and fields call and the full-tree recursion observers. The new tail-rebind
and depth probes are included. Static rejection cases are recorded but have no
executable runtime. The deliberate arena-overflow call must report `Exhausted`
in C and Wasm; it is not turned into a timing sample. Its upstream native
reference is still measured. The C gate remains the authority for independent
seed/evaluator/backend agreement, resource classifications and semantic mutants.

The [first complete tables](c-first.md) and [raw metric samples](c-first.json)
cover 46 programs / 143 frozen calls: C and Wasm each have 142 successful calls
plus one expected arena exhaustion; upstream native has 111 successful calls
and 32 unavailable calls across 14 programs. Each C/Wasm worker lane checked
1,008,200 warmup and measured invocations. For `wasm-flag`, median C emission was
3.79 ms (73.11 ms including cc), versus 3.62 ms for Wasm emission. `main()` process
latency was 2.29 ms C, 27.93 ms Node Wasm, and 3.34 ms upstream native. These are
the initial shared-host observations; the timing boundaries below matter.

```sh
BEND_NO_TELEMETRY=1 node bench/c-run.mjs
BEND_NO_TELEMETRY=1 node bench/c-run.mjs --only=wasm-flag --out=.local/bench/results/c-smoke.json
node bench/c-report.mjs .local/bench/results/c-smoke.json
node --test bench/c-tests.mjs
```

Defaults are seven runtime samples of 1,000 calls after 100 warmup calls, three
compile samples, and three process samples. Every compile/process series also
has one unmeasured warmup. Use `--repeat`, `--warmup`, `--iterations`,
`--compile-repeat`, `--process-repeat`, and `--upstream-repeat` to change these
counts. Counts must be positive. `--only=NAME` selects a manifest program;
without it the complete corpus runs. Fresh outputs and wrappers stay under
ignored `.local/bench/c-runs/`; the result path is printed. Existing result files
are never overwritten.

The driver rebuilds Knot's separate C entry and the existing fields Wasm entry
with the pinned seed as native executables. It invokes the seed with
`bun --no-env-file` and `BEND_NO_TELEMETRY=1`; no dotenv files, network services or
new dependencies are used. Generated C is built by the system `cc` with
`-O2 -std=c99 -Wall -Werror -fwrapv`. The exact `cc` and seed-native compiler
versions, source hashes, fixture hashes, manifest hash, commands, sample counts,
raw measurements, machine description and dirty Git state are retained.

| Metric | Timed work |
| --- | --- |
| C emission, ms | Native Knot compiler process reads a source and writes C |
| C cc, ms | System cc turns that generated C into a native executable |
| C total, ms | Sum of those two sequential durations |
| Wasm emission, ms | Native Knot compiler process reads the same source and writes Wasm |
| C fresh lifetime, ns/call | Reset arena/depth counters, dispatch export, invoke, check result |
| Wasm fresh lifetime, ns/call | Instantiate an already compiled module, look up export, invoke, check result |
| Process, ms/process | Start native C, Node Wasm, or upstream native executable and check its printed result |
| Upstream native build, ms | Pinned seed reads a per-call Base wrapper and builds native output with its default C11/O3 flags |

The fields Wasm profile has no reset export. A fresh instance per call is its
available reset operation, and that operation is deliberately inside the timer.
C reset is inside its timer too. These are comparable fresh-lifetime tasks, but
the reset and lookup costs differ substantially. They do **not** measure pure
generated instruction speed. Even enum cases use this same lifetime policy.
Wasm validation/module compilation, worker startup and C worker compilation are
outside these warm timers. The C worker is a separate translation unit, with no
LTO; every invocation and result check stays observable. No empty-loop cost is
subtracted. Fixed arguments can favor runtime optimization. The native clock's
reported resolution is retained; a zero-duration batch fails and requires a
larger iteration count, rather than substituting a fabricated timing.
The host is shared; the harness does not pin a CPU, lock frequency or exclude
other campaign work. Initial measurements establish a reproducible lane and a
local starting point, not an isolated performance qualification.

Upstream Bend can emit native code for compatible pure source observations. It
requires `import Base`, so each immutable manifest expression is called from a
small Base wrapper. Erased arguments come from that frozen expression. Its
native runtime exposes `main`, without a stable direct-call/reset ABI; therefore
the reference is a process lane, with no invented in-process measurement. Some
unchanged fixtures declare names such as `Pair` that conflict with Base. These
reference lanes are `unavailable`, with the exact seed diagnostic retained;
no fixture is renamed. The [import controls](c-upstream-probes.json) confirm
that omitting Base fails with `a build needs import Base`, while
`import Base as B` is rejected by the seed parser. A whole-book name collision
is checked once per program and reused for its other calls; unexpected build
errors still fail the run. The native runtime
prints a constructor while C/Wasm print JSON. Startup, scheduling, allocation
and printing costs all remain charged. Upstream can optimize its selected entry
and unreachable code; Knot currently emits all source functions. Its build
times therefore have a different compilation boundary and are reported per
call, not used as a backend-emission equivalence claim.

All runtime warmup and measured calls check the frozen result. Every emitted
artifact is exercised by successful calls; repeated C text and Wasm bytes must
be identical. Expected exhaustion is checked against the final artifact.
Unexpected failure, timeout, trap, wrong result, changed source or a compiler
without an exact `Built` receipt fails the run. Expected exhaustion remains a
separate outcome. The benchmark validates the previously frozen observations;
it never updates expectations. Generated wrappers select an entry only; the
host implements no Bend evaluator, checker or emitter.

Statistics come directly from `bench/lib/stats.mjs`: raw samples, `n`, median,
unscaled MAD and min; ratios use the existing deterministic 10,000-resample,
95% bootstrap and 2% margin. Each call and metric remains separate. Ratios are
C/reference. Fewer than three samples yields `insufficient samples`. A lower
fresh-lifetime ratio is a result for the reported host boundary, not a general
native-code speedup. The initial tiny corpus is dominated by setup on several
lanes; larger accepted workloads and a Wasm reset ABI are the next useful
measurement improvements.

`c-tests.mjs` independently checks both workers with mutable-counter controls:
omitting a reset/instance replacement makes the second call fail. It also checks
wrong-result, bad-export, bad-arity and zero-iteration rejection. The existing
benchmark suites, assertions and comparison protocol are unchanged.
