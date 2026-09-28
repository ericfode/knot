# opt-1: checked core optimization

This increment adds an optional core-to-core pipeline and a separate fields
compiler entry. It preserves the existing source checker, driver, CLIs and
emitters. Each pass changes only function bodies, rechecks its complete output,
and keeps the ordered type declarations, signatures and exports.

`src/opt.bend` composes Inline, Fold and Dead to a bounded fixed point. Small
non-recursive callees move above both caller and actual-argument level ceilings;
arguments become ordered, once-only bindings. Folding selects known constructor
arms and binds fields conservatively. DCE removes unused erased/reusable lets.
`src/opt-wasm.bend` emits `return_call` only for tail self-calls. The core verifier
permits fresh let-bound match levels without relaxing source-language matching.

The [contract](SPEC.md) fixes the regression domain. The [law review](LAW_REVIEW.md)
separates twelve checked local equations from corpus-level semantic evidence.
This is not a universal preservation proof. Every current top-level function is
exported, so function DCE retains all functions. Primitive arithmetic awaits the
literals increment. Unknown future IR constructors remain Unsupported.

## Deterministic verification

`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 2 --keep-scratch` exited **0**:
all 15 registered gates passed in 623.312408 measured seconds. The
[summary](receipts/gates.json) retains exact counts, source/dependency identities
and receipt comparisons; [stderr](receipts/gates.txt) records every gate result.
Existing gate scripts and assertions are unchanged; the runner adds one gate and
increments its registration-count assertion. Coverage categories overlap.

| Gate | Exact passing coverage |
| --- | --- |
| frontend | 14 fixtures; 28 lane observations; 24 boundaries; 4 mutants |
| checker | 49 fixtures; 98 lane observations; 10 budget probes; 2 catalog-bound records / 16 observations; 7 mutants |
| structural | 16 fixtures; 64 lane observations; 4 boundary pairs; 7 mutants |
| fields | 40 fixtures; 240 phase/lane observations; 36 budget probes; 6 host boundaries; 2 bound records / 12 observations; 9 mutants |
| wasm | 25 programs; 90 reference calls in 2 lanes; 64 rejection controls; 44 boundaries; 7 mutants |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants |
| flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes; 9 mutants |
| recursion | 19 seed fixtures; 114 check/eval/compile lane observations; 4 fuel probes; 3 mutants |
| fields-wasm | 8 programs; 32 reference calls in 2 lanes; 50 enum byte-preservation checks; 30 boundaries; 4 mutants; 5 checked laws |
| compiler-opt | 71 corpus programs (63 accepted, 8 rejected), plus 11 observer programs; 211 reference calls in 2 lanes; 43 core controls per lane; 12 checked laws; 14 boundaries; 4 mutants in both lanes |
| census | 38 compiler files; 541 declarations; 40 feature classes |
| lint:verify | 127 tests; 8 law-rule wiring controls; no provider calls |

The new gate additionally checks 148 ABIs, 148 canonical fixed points, 148 frozen
unoptimized modules, 50 default enum modules, 444 individual-pass ABIs, 1,266
individual-pass evaluator observations, 592 self-tail module inspections and 16
rejection-lane records. Its [full receipt](receipts/optimization.json) includes
all commands, source identities, observations and mutant outcomes. Every recorded
input hash still matches the final source, and every preexisting `src/*.bend`
identity matches the frozen baseline.

Full-pipeline evaluation records 420 successful observations and 2 parser-budget
Exhausted observations **per setting** (off/on), across both lanes. Wasm records
398 successful off observations plus 2 arena exhaustions, and 400 successful on
observations. Structured outputs use the exact-tree observers. Resource
exhaustion is not counted as a matching semantic value.

Of 81 regenerated artifacts, 63 are identical, 10 volatile-only and 8 semantic.
The eight are the new optimization receipt and seven existing receipts whose
differences are input identities only, including stale host-script identities.
Shared receipts remain untouched for the coordinator's integration refresh.

`npm run -s gates:verify` passed all 18 wrapper tests, including six semantic
mutants. `npm run bench:verify` passed 39 tests and the default native/Bun smoke
run. `src/opt-PROOF.bend` printed `All terms check.` with all twelve new laws
filled; its import chain includes the prior recursion proofs.

## Fixed fixtures and mutants

Six primary fixtures fixed 24 literal/seed calls before optimizer implementation:
known cases, lexical capture, used lets, known fields, tail recursion and non-tail
recursion. Four review regressions add 23 independently seeded calls: nested
actual locals, nullary callee locals, constructor-field scope, and erased forward
calls. Eleven observer fixtures append frozen complete-tree recognizers to the
accepted recursion programs; their 22 calls include a near miss for each tree.
The host observes enums and never interprets pointers. Nine generated programs
cover enum width, match width and acyclic call depth at 16, 64 and 128.

Four source-level type-correct compiler mutants are checked and built in both
native and Bun: wrong case arm, deletion of a used let, captured wrong level and
deleted export. The middle two fail the precise checked-core preservation
diagnostic; the others violate the fixed result/export contract. Host failures,
timeouts and failure to build do not count as semantic kills.

The [development-failure record](receipts/development-failure.json) retains the
intermediate Bun stack failure caused by whole-book textual equality. Bounded
structural comparison resolves it. The overwritten intermediate binary has no
retained hash; the historical record states that provenance limit.

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

## Style preflight

[Offline preflight](receipts/preflight.json) ran on all 33 new Bend files with the
fixed task supplied: 379 declarations, zero unranked or empty files, zero provider
requests. It exited **3** with 73 structural blockers: 72 truncated unit contexts
and unavailable composition. Truncation reasons overlap: 19 caller/byte, 12 file
and 49 helper-limit cases. Supporting-role classification is unavailable for 75
units. Composition needs 177,918 bytes against 48,000 and has unresolved imports
and collaborators. All five ratings—conceptual compression, Delight, memetic
identity, Anticipation and Payoff—and Galaxy brain remain unavailable. No style
pass is claimed. The manifest adds five source groups with complete local import
closures; larger groups still exceed the composition bound. The
[first full run](receipts/gates-first.json) exposed missing import closure in
these new groups ([test output](receipts/manifest-failure.txt)). The manifest was
fixed, and its unchanged coverage/closure test then passed.

Fresh preflight of the corrected groups also exits 3 in each group. Counts below
include unchanged collaborators and overlap across groups; they are not added.
Inline and Fold have complete composition packets, while their declaration
contexts still have truncation blockers.

| Group | Declarations | Truncated | Composition bytes / availability |
| --- | ---: | ---: | --- |
| [opt-check](receipts/preflight-opt-check.json) | 167 | 30 | 64,048 / oversized |
| [opt-inline](receipts/preflight-opt-inline.json) | 54 | 11 | 16,080 / available |
| [opt-fold](receipts/preflight-opt-fold.json) | 63 | 11 | 18,425 / available |
| [opt-pipeline](receipts/preflight-opt-pipeline.json) | 426 | 50 | 145,804 / oversized, external context |
| [opt-wasm](receipts/preflight-opt-wasm.json) | 197 | 34 | 73,624 / oversized, external context |

## Limits and integration

The checked transformation is bounded to 32-node callees, levels below 4,096 and
eight fixed-point rounds. Fusion refuses scope conflicts and residual parent
uses; affine lets remain. Stack, evaluator fuel and arena exhaustion are separate
resource observations. Eliminating work can turn exhaustion into a successful
value. The fields arena and ABI are unchanged, including their existing limits.
Field-allocation timing needs an explicit instance-lifetime protocol before it
can enter the warm-call benchmark.

The coordinator should run bounded live Perch review and refresh shared receipts
after integration. The next optimization increment should target the measured
compile/size costs with a whole-body growth budget and a frozen benchmark
comparison. Nest, modules, literals and private exports need fresh domains and
gates as their IR support arrives. Baseline source identities are audit evidence;
frozen unoptimized module bytes and behavior remain hard assertions.

Reproduction:

```sh
export BEND_NO_TELEMETRY=1
npm run -s gates -- --jobs 2 --keep-scratch
npm run -s gates:verify
npm run bench:verify
npm run bench -- --suite=opt --pipeline=off --out=.local/opt-off.json
npm run bench -- --suite=opt --pipeline=on --out=.local/opt-on.json
npm run bench:compare -- .local/opt-off.json .local/opt-on.json
```
