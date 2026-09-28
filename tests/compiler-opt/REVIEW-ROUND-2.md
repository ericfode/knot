# opt-1 review round 2

This increment preserves the original frozen expectations, baseline module
hashes, twelve laws, 43 core controls and the original corpus's fixed-point
assertions. The three added regression fixtures and their eleven seed/off-path
observations were committed before the optimizer repairs.

## Findings

| Confirmed finding | Disposition and evidence |
| --- | --- |
| Raw scratch receipts | **Fixed.** `6b09151` replaces the original 7,549,118-byte receipt with the byte-identical 6,479,495-byte runner-normalized copy and normalizes nine smaller evidence files. Current direct runs normalize before writing; full IR is compared before retaining its hash and length. The final receipt is copied from the runner's `normalized/` tree. |
| Frozen shared-corpus size/source/generator | **Fixed.** The gate reads all three manifests and the current generator on every run. Prior off hashes remain mandatory; new entries run the same differentials and are explicitly listed until frozen. `freeze.py --case KEY --append` adds independently checked entries to `extensions.json` and rejects replacements. Eight offline controls and the isolated growth receipt exercise the extension procedure. |
| Empty-book mutant counted through HostFailure | **Fixed.** Every pass compares ordered input/output export names, parameter quantities/types and result types before checking its output bodies. The original all-function mutant is caught by that recheck. A separate type-correct emitter mutant omits only `choose`, retains a successful `main`, and is killed by independently decoded ABI inequality against the frozen off ABI. Its missing-export HostFailure is recorded separately. |
| Oversized style packets | **Fixed for bounded review.** All five manifest groups and all 29 test-file packets have zero structural blockers under main's `interfaces-v1` policy. No frozen observer or declaration is excluded. The exact combined command remains blocked; the full limits below remain part of this handoff. |
| Eight rounds reject successful programs | **Fixed.** A positive round budget returns its last checked result at the work cap. The existing direct zero-round Exhausted law remains unchanged. `r_4_13` and `r_20_13` must compile and agree at both default and maximum CLI budgets even when another pipeline application can make progress. |
| Fold duplicates shared boxed values | **Fixed.** Both literal caching and reference substitution require an enum-only datatype. `arena-sharing` preserves successful seed/evaluator/Wasm observations under Fold alone and the complete pipeline. The before receipt reproduces the original Fold-only arena exhaustion; DCE was not required to trigger it. |

No confirmed finding is disputed. These are bounded repairs and evidence, not a
universal optimization-preservation theorem or an automatic D9 style pass.

## Independent controls and mutations

[`regressions.json`](regressions.json) freezes `r_4_13`, `r_20_13` and
`arena-sharing`, with 5, 5 and 1 successful calls respectively. Their off modules
are 215, 548 and 3,891 bytes. The separate ABI control freezes `known`'s
`choose(i32) -> i32` and `main() -> i32` exports. The
[before receipt](receipts/regressions-before.json) identifies the original
source snapshot and independently rebuilt failing binaries.

Four additional filled laws cover final-round stopping, enum propagation,
boxed-value retention and missing-export rejection. Fourteen literal review
controls per execution lane cover unchanged, removed, reordered, renamed and
type/quantity-modified exports, body rechecking, enum/boxed references and
round limits. Existing core controls and frozen expectations are unchanged.

All seven source mutants must typecheck and build in both execution lanes:

| Mutant | Required kill, in each lane |
| --- | --- |
| `case-wrong-arm` | Wrong successful result: `semantic-kill` |
| `dce-used-let` | `binding-level`: `checked-core-preservation-kill` |
| `inline-capture` | `affine-reuse`: `checked-core-preservation-kill` |
| `dce-all-exports` | `exports-changed`: `checked-core-preservation-kill` |
| `rounds-exhaustion` | Previously successful chain exhausts: `optimization-availability-kill` |
| `boxed-duplication` | Previously successful arena call exhausts: `resource-preservation-kill` |
| `one-export` | Exactly one frozen export missing, retained entry succeeds: `abi-kill` |

Failed builds, timeouts and unrelated host failures do not satisfy these
obligations. Invalid, Unsupported, Exhausted, HostFailure and InternalFailure
remain separate observations.

The isolated [growth run](receipts/corpus-growth.json) adds one enum case, one
Unsupported case, three generated benchmarks and one filled law, and changes
only a comment in an existing shared fixture. Its gate passes with 79 source
programs (70 accepted, 9 rejected), 11 observers, 228 reference calls, 17 laws,
162 ABI checks, 486 single-pass ABI checks, 1,368 single-pass evaluator checks,
154 frozen byte checks and seven mutants in both lanes. All four new positive
cases are reported as unfrozen. The final freezer then appends one selected
entry after three independent calls in both lanes. Existing baseline,
expectations and regressions remain byte-identical. This run used the recorded
earlier harness snapshot. The final gate additionally runs the maximum-budget
chain probes, eight corpus controls, fourteen review controls per lane and
extension-observer hash checks; those additions are not claimed for the growth
run. Final freezer inputs, broader input identities and the law-domain widening
are recorded separately. Corpus loading and differential mechanisms are
unchanged between these snapshots. No production corpus was edited.

## Verification

The complete runner exits 0 with **18/18 gates passed**:

```sh
BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1 --timeout 1800
BEND_NO_TELEMETRY=1 npm run -s gates:verify
```

The wrapper verification command passed **18 tests**, including the six wrapper
mutants; its implementation is unchanged since that check in this increment.
All sixteen optimizer laws print `All terms check.` through the complete proof
entry. Counts below are the runner's categories; overlapping categories are
not summed into one assertion total. The [compact gate receipt](receipts/gates-review2.json)
retains commands, snapshot/dependency hashes and measured durations. Total
measured wall time is **874.705277 seconds**.

| Gate | Exact passed coverage |
| --- | --- |
| frontend | boundaries: 24; fixtures: 14; lane observations: 28; mutants: 4 |
| checker | bound observations: 16; bounds: 2; budgets: 10; fixtures: 49; lane observations: 98; mutants: 7 |
| structural | bounds: 4; fixtures: 16; lane observations: 64; mutants: 7 |
| fields | bound observations: 12; bounds: 2; budgets: 36; fixtures: 40; host boundaries: 6; lane observations: 240; mutants: 9 |
| wasm | boundaries: 44; execution lanes: 2; fixtures: 25; mutants: 7; reference calls: 90; rejects: 64 |
| wasm-trust | entries: 3; proof holes: 0 |
| fields-trust | entries: 4; proof holes: 0 |
| structural-trust | entries: 2; proof holes: 0 |
| owned-store | cases: 3532; execution lanes: 2; literal witnesses: 15; mutants: 6 |
| flat-store | bun [installed boundary states: 2; instances: 3534; lifecycle checks: 7; observations: 13621]; mutants: 9; native [installed boundary states: 2; instances: 3534; lifecycle checks: 7; observations: 13621] |
| recursion | fixtures: 19; mutants: 3 |
| fields-wasm | boundaries: 30; fixtures: 8; mutants: 4 |
| compiler-opt | abi checks: 154; accepted programs: 66; boundaries: 18; core idempotence checks: 148; core round observations: 154; core verifier controls per lane: 43; corpus growth controls: 8; default enum byte checks: 50; direct pointer host calls: 0; execution lanes: 2; generated programs: 9; new fixture reference calls: 58; new fixtures: 13; new laws: 16; observer programs: 11; observer reference calls: 22; reference calls: 222; rejected programs: 8; rejection lane observations: 16; review controls per lane: 14; self tail module checks: 616; semantic mutants: 7; single pass abi checks: 462; single pass evaluator checks: 1332; source programs: 74; structured result observers: 22; unfrozen off programs: 0; unoptimized byte checks: 154 |
| census | classes: 41; declarations: 567; files: 38 |
| perch-context | fixtures: 33; mutants: 8 |
| lint:verify | law rules: 8; tests: 168 |
| bootstrap | corpus: 660; mutants: 9; reached: 2; stages: 8 |
| classification | fixtures: 17; mutants: 6 |

The bootstrap harness passes with two reached stages and six classified blocked
stages; this does not establish compiler self-hosting. The ordinary optimizer
corpus has no unfrozen off-byte entries. Both slow chains agree despite their
non-idempotent bounded result. The shared arena fixture succeeds under Fold
alone and the full pipeline in both compiler lanes.

The final optimizer receipt is **5,937,017 bytes**, copied from the runner's
`normalized/` tree with SHA-256 `fa97cadd5f35295f48999386aaef52c4df6be766cbc10d6dbd1d3651ce113bef`. All **142** recorded
input hashes match the final working sources. Re-normalizing against an unrelated
future scratch root leaves identical bytes and zero changed fields. All optimizer
receipt/evidence files contain zero absolute user-home paths. Original frozen
files and the separately committed new expectations are byte-identical to their
respective checkpoints.

The earlier [four-worker run](receipts/gates-review2-first.json) remains failed:
16 gates passed, frontend could not discover Clang during a native seed build,
and compiler-opt hit the runner's 900-second wall guard during mutant checking.
The sequential complete run uses a 1,800-second harness guard; no compiler
budget, frozen expectation or semantic assertion changed. Its optimizer gate
finished in **427.320674 seconds**,
below the original 900-second guard. Shared receipts were not refreshed in this
worktree.

## Offline style review

The [packet report](STYLE-REVIEW.md) and its two receipts retain all commands,
source/package identities and context limits. All **34/34** bounded/file
preflights exit 0, with zero blockers and provider requests. The five groups
contain 315 declaration obligations, covering 163 distinct declarations;
29 complete test-file packets cover 309 declarations. The pipeline composition
is **41,536 / 48,000 bytes**. The unchanged manifest tests pass **24/24**.

Both exact combined selections cover 37 files and 439 declarations and exit 3:
**81 structural blockers**, including 80 truncated contexts, plus 83 declarations
without complete role context. The composition requires **186,307 / 48,000
bytes**. The plain command lacks task context; the task-qualified command still
has the same structural blockers. This aggregate is not a qualified composition.

Conceptual compression, Delight, memetic identity, Anticipation, Payoff and
potential profundity are **unrated**. Offline readiness does not supply model
distributions or satisfy their quality bars. Live review belongs to the
coordinator; no provider request was made.

## Checkpoints and limits

- `2ac3fcc`: merge current main, preserving both gate inventories and review logs.
- `6b09151`: normalize historical optimizer receipts without changing observations.
- `8cdf4a0`: freeze the new seed and unoptimized regression expectations.
- The repair checkpoint containing this report includes the code, controls,
  bounded packets, regenerated census and final optimizer receipt. Its message
  includes every printed census approval.

The work cap can return a checked non-fixed-point result. Inlining still has its
32-node callee and 4,096-level bounds. There is no universal preservation proof,
generalized recursion, primitive arithmetic, private-function metadata or arena
reclamation. The historical benchmark receipts describe the original optimizer;
they do not measure these repairs. No new speedup claim is made.

The next increment needs coordinator integration and shared-receipt refresh,
live review of the complete bounded mechanisms, and fresh performance/size
measurements if optimization policy is to change. Corpus extensions should use
the documented explicit freeze procedure while retaining prior off hashes.
