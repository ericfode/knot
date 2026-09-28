# bench-2 handoff

All changes are under `bench/`. Compiler sources, existing fixtures and
expectations, package files, the gate runner and shared receipts are unchanged.

The default `hillclimb` suite discovers 189 frozen programs across recursion,
fields-wasm, closures, baseslice, generics and literals, plus 12 deterministic
programs. Every run probes both compiler lanes. There are currently **31
measured programs, 157 Unsupported and 13 Invalid**. Five of those Invalid
results contradict seed acceptance and are explicitly recorded as D4
classification discrepancies; no unavailable capability is called accepted.

The new generators cover Peano recursion, lists of fielded cells, wide matches
and many small functions at sizes 32/96/192. Results were fixed by literal
review first and then checked against the pinned seed, both evaluator lanes and
Wasm. List construction is chunked to preserve 192 runtime cells within the
parser's default depth. `second-descent` has an additional seed-backed literal
observation so its evaluator timer can activate when support lands.

Both enum and fields Wasm profiles have warmup, in-process batches and per-call
result checks. Every new runtime batch lasts at least 10 ms; this is a **batch
iteration**, not a promise that one source invocation lasts 10 ms. Fields calls
include fresh-instance cost because their arena has no reset. Whole compiler
and evaluator CLI timers retain the phases included and the reason individual
phase clocks are unavailable. Named baselines and compatibility-checked,
noise-aware comparisons are documented in [HILLCLIMB.md](HILLCLIMB.md).

## Validation

`npm run bench:verify` passed **53 unit tests**, the original two-lane enum
smoke, and the complete 201-program inventory in both lanes. Its new execution
gate measured 31 programs and **38 runtime batches >=10 ms** (19 programs × two
compiler lanes). Eleven recursion fixtures have structured results outside the
host ABI. The arena-overflow fixture compiles but exhausts at runtime. The
deep-call fixture runs from Wasm but its evaluator exhausts its parser budget.

Four semantic mutants were checked by the seed (`All terms check.`), compiled
in both lanes, and killed by the fixed result guard: **odd-base**, **ignore-cell**,
**wrong-arm**, and **omit-flip**. All eight mutant executions were rejected for a
wrong result, not a syntax/type error or a trap. Independent worker controls
also catch instance reuse and a wrong timed call after successful validation
and warmup. Receipts: [verification](receipts/verification.json),
[validation](receipts/validation.json).

All 14 registered gates passed through the unmodified runner, exit 0.
`npm run -s gates:verify` passed all **18 tests**. Exact categories are retained
below; categories overlap and are not summed into one assertion count.

| Gate | Passed counts |
| --- | --- |
| frontend | 14 seed fixtures, 28 parser observations, 24 boundaries, 4 boundary laws, 6 classification laws, 4 semantic mutants; 12 classification fixtures in 2 lanes, 7 classification mutants, 72 downstream rejection observations |
| checker | 49 fixtures, 98 lane observations, 10 budget probes, 2 bounds / 16 bound observations, 7 mutants |
| structural | 16 fixtures, 64 lane observations, 4 bounds, 7 mutants |
| fields | 40 fixtures, 240 phase observations, 36 budget probes, 6 host boundaries, 2 bounds / 12 bound observations, 9 mutants |
| wasm | 25 programs, 90 seed calls, 2 execution lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| wasm-trust | 3 entries, 0 proof holes |
| fields-trust | 4 entries, 0 proof holes |
| structural-trust | 2 entries, 0 proof holes |
| owned-store | 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| flat-store | Each lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes, 9 mutants |
| recursion | 19 seed fixtures, 114 phase observations, 4 fuel probes, 3 mutants |
| fields-wasm | 8 fixtures, 32 seed calls, 64 evaluator observations, 64 Node observations, 50 frozen enum-byte checks, 30 boundary probes, 4 mutants in both lanes, 5 checked laws |
| census | Current: 30 compiler files, 425 declarations, 40 feature classes; no new source/import/feature class to approve |
| lint:verify | 127 tests, 8 law-rule wiring controls, no provider calls |

The successful scratch run took **369.329453 seconds** and reported **63
identical, 17 volatile-only and 0 semantic** receipt differences. No shared
receipt was refreshed. The first four-worker attempt had two host failures
(frontend's 30-second seed-build timeout and a seed clang-discovery failure).
A serial attempt retained the frontend timeout. The successful serial command
selected the installed Xcode clang and SDK explicitly, without changing a
compiler, gate, assertion or timeout:

```sh
export BEND_NO_TELEMETRY=1
export SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.5.sdk
export PATH=/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin:$PATH
npm run -s gates -- --jobs 1
npm run -s gates:verify
```

## Preflight and remaining work

Offline preflight ran separately on all 12 generated Bend files: **378
declarations**, **204 truncated contexts**, all **12 compositions available**,
zero unranked files, and **0 provider requests**. Seven files exit 0; five exit 3:
`cells-96` (1 truncated unit), `cells-192` (1), `inline-32` (2), `inline-96` (52),
`inline-192` (148). The intentional scale is retained. This is not a style pass;
compression, delight, memetic identity, anticipation and payoff have no live
ratings. [Per-file receipts and summary](receipts/preflight.json).

The coordinator's next steps are to review/merge this increment, register
`bench:verify` in the gate runner if desired, and perform live Perch review.
Registration is deliberately left to the coordinator because bench-2 explicitly
forbids editing that runner. No new production Bend file or law needs a manifest
group or proof entry.

Compiler-owner follow-ups: the seed-valid closure fixtures `return-closure`,
`closure-in-arm`, `defunc-sites`, and `curried-arities` currently report
`Invalid parse function-result`; `closure-drop` reports `Invalid parse expected-=`.
All five remain visible in benchmark receipts. Structured host observations,
arena reset/reclamation, isolated phase clocks and generalized recursive Wasm
qualification remain compiler/runtime work. New capability coverage requires a
fresh comparison baseline; the suites discover its acceptance automatically.
