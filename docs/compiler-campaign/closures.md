# Closure increment

Monomorphic closures are implemented in Bend: arrow types, affine and erased
captures, named and partial function values, nested/returned closures,
function-valued fields/lists and CPS. `closure-types.bend` owns arrow identity;
`closure-check.bend` owns capture/partial-application construction;
`closure.bend` defunctionalizes each used arrow into a constructor family and
an apply dispatcher. Core additions are one Arrow datatype variant plus Closure
and Invoke terms. The evaluator independently stores environments. Wasm retains
`knot-fields-wasm-1` cells and uses `return_call` in actual tail positions.

Ordinary exact-arity calls retain the old checker-depth contract. All earlier
assertions remain unchanged except the separately committed, seed-backed
structural/function-field catalog pin. Its source and seed result are unchanged.
The original 42 closure fixtures, observations, expectations and `regen.py` are
unchanged. Arrow metadata alone preserves the old enum Wasm bytes.

Expectation-first checkpoints:

- `61554f7`: structural/function-field accepted catalog pin, with seed evidence.
- `3d7efa2`: exact erased-cell layout and deep-continuation probes.
- `9060cf1`: nine seed-fixed review regressions before boundary repairs.
- `6253fd5`: literal-lambda scrutinee rejection before repair.
- `1f4ff7e`: global `_()` visibility beneath a discarded binder before repair.

The implementation checkpoint contains the source, proofs, gate, own receipts,
manifest groups, census approval and this report. No push, merge or rebase belongs
to this executor. The coordinator owns integration and shared receipt refresh.

## Independent evidence

Both `BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1` and
`npm run -s gates:verify` exit 0. The complete runner has 15 passed gates.
Counts below overlap and are not summed into an assertion total. Commands,
source/dependency snapshot hashes and exact completion records are retained in
[`receipts/gates.json`](../../tests/compiler-closures/receipts/gates.json).
The raw run is `.local/gates/run-irwij8mp/`.

| Gate | Exact passed coverage |
| --- | --- |
| frontend | 14 fixtures, 28 parser-lane observations, 24 boundaries, 4 mutants; classification: 12 fixtures in 2 lanes, 7 mutants, 72 downstream rejection observations; 4 boundary and 6 classification laws |
| checker | 49 fixtures, 98 checked observations, 10 depth probes, 16 catalog-bound observations, 7 mutants |
| structural | 16 fixtures, 64 phase/lane observations, 4 boundary pairs, 7 mutants |
| fields | 40 fixtures, 240 phase/lane observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants |
| wasm | 25 programs, 90 reference calls in 2 lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| wasm-trust | 3 entries, 0 proof holes |
| fields-trust | 4 entries, 0 proof holes |
| structural-trust | 2 entries, 0 proof holes |
| owned-store | 3,532 cases in 2 lanes, 15 literal witnesses, 6 mutants |
| flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes, 9 mutants |
| recursion | 19 fixtures, 114 phase/lane observations, 4 fuel probes, 3 mutants |
| fields-wasm | 8 fixtures, 32 seed calls, 64 evaluator and 64 Node observations, 50 enum-byte checks, 30 boundaries, 4 mutants killed in both lanes, 5 checked laws |
| census | 39 compiler files, 581 declarations, 501 unique declarations, 372 definitions, 40 feature classes |
| lint:verify | 127 tests, 8 law-rule wiring controls, 0 provider calls |
| closures | 55 sources: 29 agree, 25 expected rejections, 1 blocked; 110 check and 110 compile observations, 52 rejection/block evaluator observations; 538 evaluator and 538 Node calls; 29 byte comparisons, 14 boundaries, 5 mutants / 10 lane kills; 3 proof entries / 24 checked laws |

Gate-runner verification separately passes 18 tests, including six executable
wrapper mutants. `regen.py` still passes all 42 original fixtures and 292 seed
calls. The closure gate additionally reruns two probes / eight calls and eleven
regressions / eight calls / three seed rejections (66 regression phase
observations). Its blocked fixture is recorded as blocked, not passed.

Of 81 regenerated receipt artifacts, 63 are identical, seven volatile-only and
11 semantic. Existing shared receipts are untouched in this worktree; their
source/inventory refresh remains with the coordinator. Only this increment's
new closure, preflight and full-run summary receipts are committed.

Nine complete root `src/` proof entries print `All terms check.` The three new
entries fill 24 laws. These establish local type, quantity, lowering and machine
transition equations. Seed/evaluator/Wasm agreement is finite corpus evidence,
not a general compiler-correctness or memory-refinement theorem. The law review
packet is [here](../../tests/compiler-closures/LAW_REVIEW.md).

Of the 292 original seed calls, 253 have matching Knot evaluator and Wasm
observations. Nineteen remain blocked on generics; the other 20 belong to the
explicit Unsupported template/do/dependent-arrow/lambda-match boundaries. The
55 total sources classify as 29 accepted, 20 Invalid and six Unsupported
(including the one blocked fixture).

Two supplemental sources add eight seed calls. The erased-layout control fills
exactly 8,192 two-word cells in the unchanged 64-KiB arena, then traps before
advancing allocation. The continuation control invokes 2,048 affine closures
under the constrained Node stack. Eleven review regressions add eight accepted
calls and three seed rejections, with 22 exact check/run seed observations.
They cover discarded binders and global names, computed scrutinees, erased and
nested captures, reconstructed parents, partial calls and empty application.

Five type-correct mutants are killed in both compiler lanes: wrong dispatch arm,
dropped capture, duplicated affine capture, erased capture stored live, and a
tail call changed to an ordinary call. The last requires its shallow control to
pass before deep stack exhaustion counts as a kill. The layout mutant preserves
result values but exhausts at 5,461 cells rather than 8,192. Crashes, unrelated
rejections and timeouts cannot satisfy these mutant checks.

The first full scratch run failed the old fields checker-depth boundary and
blocked fields-trust; the other gates, including closures, passed. A second
parallel run hit native-build timeouts and one seed clang-discovery failure.
These retained host failures are distinct from source outcomes. The repair
preserves the old direct path for exact-arity named calls. The final scratch run
supersedes both failed runs without changing the boundary assertions. Earlier
concurrent exploratory closure runs refused completion when inputs changed;
those incomplete receipts do not supply acceptance evidence.

## Offline preflight

All 33 changed Bend files were selected. The pinned parser rejects the two
intentionally invalid scrutinee fixtures; their source hashes and exclusions
are retained in `receipts/preflight-selection.json`. The remaining 31 files
have 458 parsed declarations. Offline preflight exits 3 with 63 truncated
contexts, 88 incomplete role contexts, and an unavailable aggregate composition
(over the 48,000-byte bound and containing unresolved context).

| Bounded manifest family | Declarations | Truncated contexts | Composition |
| --- | ---: | ---: | --- |
| closure-types | 67 | 14 | Available, 15,866 bytes |
| closure-checking | 200 | 30 | Unavailable, 67,866 bytes |
| closure-lowering | 80 | 15 | Available, 20,401 bytes |

Each bounded preflight also exits 3. There were zero provider requests.
Compression / Maximally big brain, Delight, memetic identity, Anticipation and
Payoff have no model ratings or distributions from an offline run. None is
reported as meeting its quality target; potential profundity/Galaxy brain also
remains unjudged. The coordinator must resolve context limits and run live
source and law-packet review. Preflight receipts are retained beside the
[closure receipt](../../tests/compiler-closures/receipts/closures.json).

## Limits and integration

`generic-choose-bind` keeps its frozen agree requirement and 19 blocked calls.
Templates, dependent arrows, do-notation, lambda-match shorthand and partial
application with an erased remaining parameter retain explicit Unsupported
boundaries. Lambdas need an expected arrow; matches in lambda bodies follow the
seed's restricted binder rules. The type registry, lexical levels and emitter
traversals are bounded. The 64-KiB arena still has no reclamation.

Only enum-only signatures cross the Wasm host boundary. Function arguments and
results are internal; eval-cli reports HostFailure for those host requests.
A dispatcher with no source inhabitant sites is unreachable under that host
precondition; forged function handles are outside it. GPU lowering, C closure
lowering and a universal defunctionalization proof are not established here.

The coordinator should reconcile the shared parse/check/eval/Wasm edits with
nest and modules, add generics before rerunning the blocked fixture, and retain
the deterministic gates during integration. The unchanged nest/closure-parameter
and generics/closure-apply pins still name old function-type Unsupported outcomes
and require their owners' reconciliation. The structural/function-field pin is
the only amended existing assertion; see [its record](closures-amendments.md).
