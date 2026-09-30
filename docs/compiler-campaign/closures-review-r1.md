# Closures review round one

The compiler repairs reject split `->`/`=>`, refuse lexical type shadows as
`Unsupported check dependent-type`, accept the seed's lambda continuations and
newlines before `=>`, intern arrows by resolved domain/result IDs, and lower
wide tail calls compatibly with Node 22.22.3 arm64. The two split-operator majors
are duplicates with one repair. The previously unverified wide-call finding is
confirmed: fresh native/Bun compilers at `c0cc612a` emitted modules that abort
default Node with SIGTRAP at widths 39 and 64, while width 38, Bun and Node
`--no-liftoff` succeed. It is fixed by a conservative 32-live-parameter bound at
both ends of `return_call`; wider callees use `call; return`, and wider callers
use ordinary body lowering. This keeps values but does not promise constant
stack usage for wide signatures. Narrow continuation acceptance remains required.

Expectation-first commit `662c88bb` adds 42 sources: 29 accepted controls and
13 seed rejections, independently observed with 42 checks, 84 native/Bun builds
and 58 seed executions. Existing expectations, fixtures, laws and mutants remain
unchanged. No seed-derived amendment to an existing expectation was needed.
The [new manifest](../../tests/compiler-closures/review-r1.json) and
[archived pre-repair receipt](../../tests/compiler-closures/receipts/history/review-r1-before.json)
retain complete sources, commands, outputs, hashes and measured timings.

Both repaired compiler lanes pass all 42 controls: 84 check, 84 evaluator and
84 compile observations, 58 default-Node calls, 29 byte comparisons, and 18
additional wide-host controls (forced Liftoff, no Liftoff and Bun). All eleven
lambda layout programs execute their seed-fixed result. Seven lexical shadow
programs refuse without creating an artifact, and their renamed controls agree.
Five new local laws check operator spans and exact arrow keys; all ten complete
root proof entries check without holes. The open general preservation obligation
remains required under D21.

The first repaired observation measured native medians over three samples:

| Unused signature | Before | After | Module bytes |
| --- | ---: | ---: | --- |
| 128 parameters | 1.849915 s | 0.005539 s | Identical, 186 bytes |
| 192 parameters | 9.834378 s | 0.008107 s | Identical, 250 bytes |

These are paired, bounded observations from seed-native `-O1` compiler builds,
with the SDK path explicit, and a 30-second external guard. They are not a
complexity theorem or a default-`-O3` performance claim. Recursive name printing
is removed from nominal/arrow lookup; explicit arrow IDs retain their existing
ordering and synthetic suffixes retain the existing inventory contract.

Four additional type-correct mutants exercise wrong split-operator acceptance,
ignored lexical type scope and false Invalid semicolon layouts. A fifth restores
wide `return_call` and is killed by decoded unsafe lowering before invocation;
host aborts are never semantic kills. The final suite kills the first four in
both lanes (eight semantic kills), and the fifth in both lanes (two lowering
safety kills). The existing five mutants and ten lane kills, plus three precheck
mutants and six lane kills, also pass unchanged. The three minor archived
receipt links in `docs/perch-review-log.md` now resolve through `receipts/history/`.

The first registered run exposed a low-level API regression: its unchanged
synthetic parameter-list boundary uses a binder with the same spelling as its
type, without representing a source scope. `catalog.parameters` retains that
explicit-list contract; source `collect_signatures` selects lexical validation.
Both original 256/257 native/Bun boundary observations and fourteen scope
programs pass after the repair. The first run was stopped after its confirmed
checker failure; its exact logs are archived, never counted as acceptance.
The [failed-run archive](../../tests/compiler-closures/receipts/history/review-r1-first-gates.json)
retains the failure before the compatibility repair in `5d702d85`.

Seven supplemental scratch probes at `40db7f0e` check both ends of the 32-argument boundary
and a 65-parameter signature with 64 erased arguments. Six agree across the
seed, native/Bun evaluators and forced-Liftoff Wasm. A 256-argument source agrees
seed/Wasm with explicit parser depth 4,096; default-depth parsing/evaluation
reports Exhausted and remains inconclusive, with its bound unchanged.

## Deterministic acceptance

The full registered suite at `5d702d85` passes all fifteen gates, each with exit
0. The command was `npm run -s gates -- --jobs 1 --timeout 1800 --keep-scratch`;
the accepted run is `.local/gates/run-9w88rwgm`, measured at 777.674703 seconds.
It used `BEND_NO_TELEMETRY=1`, the existing ignored clang `-O1` wrapper,
`TMPDIR=$PWD/.local/closures/scratch`, and explicit
`SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk`.
The receipt records this build mode; performance observations cover these
`-O1` compiler binaries.

The [full owned receipt](../../tests/compiler-closures/receipts/closures.json)
and [per-gate receipt](../../tests/compiler-closures/receipts/gates.json) preserve
the exact observations. Recording and verification pass with 217 current input
hashes and fifteen registered gates. `npm run -s gates:verify` separately passes
18 runner tests. Final signature medians are 0.006919 and 0.008642 seconds for
128 and 192 parameters respectively, with the same pre-repair module hashes.
The [scope audit](../../tests/compiler-closures/receipts/review-r1-scope.json)
checks 128 unchanged existing closure control files and eighteen preserved
law/proof files; two of the latter have append-only additions. Shared gate
scripts and other packages' frozen controls are unchanged.

| Gate | Result | Exact counts |
| --- | --- | --- |
| frontend | passed, exit 0 | `{"boundaries": 24, "fixtures": 14, "lane_observations": 28, "mutants": 4}` |
| checker | passed, exit 0 | `{"bound_observations": 16, "bounds": 2, "budgets": 10, "fixtures": 49, "lane_observations": 98, "mutants": 7}` |
| structural | passed, exit 0 | `{"bounds": 4, "fixtures": 16, "lane_observations": 64, "mutants": 7}` |
| fields | passed, exit 0 | `{"bound_observations": 12, "bounds": 2, "budgets": 36, "fixtures": 40, "host_boundaries": 6, "lane_observations": 240, "mutants": 9}` |
| wasm | passed, exit 0 | `{"boundaries": 44, "execution_lanes": 2, "fixtures": 25, "mutants": 7, "reference_calls": 90, "rejects": 64}` |
| wasm-trust | passed, exit 0 | `{"entries": 3, "proof_holes": 0}` |
| fields-trust | passed, exit 0 | `{"entries": 4, "proof_holes": 0}` |
| structural-trust | passed, exit 0 | `{"entries": 2, "proof_holes": 0}` |
| owned-store | passed, exit 0 | `{"cases": 3532, "execution_lanes": 2, "literal_witnesses": 15, "mutants": 6}` |
| flat-store | passed, exit 0 | `{"bun": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}, "mutants": 9, "native": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}}` |
| recursion | passed, exit 0 | `{"fixtures": 19, "mutants": 3}` |
| fields-wasm | passed, exit 0 | `{"boundaries": 30, "fixtures": 8, "mutants": 4}` |
| census | passed, exit 0 | `{"classes": 40, "declarations": 620, "files": 42}` |
| lint:verify | passed, exit 0 | `{"law_rules": 8, "tests": 127}` |
| closures | passed, exit 0 | `{"agreed_fixtures": 49, "blocked_calls": 19, "blocked_fixtures": 1, "boundaries": 14, "boundary_probes": 14, "byte_identity_checks": 49, "check_observations": 174, "checked_laws": 33, "compile_observations": 174, "evaluator_calls": 578, "fixtures": 87, "frozen_fixtures": 42, "mutant_lane_kills": 10, "mutants": 5, "proof_entries": 4, "refresh_fixtures": 32, "refresh_phase_observations": 192, "refresh_seed_builds": 64, "refresh_seed_calls": 40, "refresh_seed_checks": 32, "refresh_seed_rejections": 12, "regression_fixtures": 11, "regression_phase_observations": 66, "regression_seed_calls": 8, "regression_seed_rejections": 3, "rejected_fixtures": 37, "rejection_evaluator_observations": 76, "seed_calls": 292, "seed_rejections": 18, "supplemental_probes": 2, "supplemental_seed_calls": 8, "wasm_calls": 578}` |

The closure gate also records these exact nested counts:

| Control family | Counts |
| --- | --- |
| prechecks | `{"byte_identity_checks": 6, "check_observations": 52, "compile_observations": 52, "eval_observations": 46, "host_result_refusals": 2, "mutant_lane_kills": 6, "mutants": 3, "parse_observations": 52, "programs": 26, "wasm_calls": 4}` |
| review_r1 | `{"agreed_fixtures": 29, "byte_identity_checks": 29, "check_observations": 84, "compile_observations": 84, "evaluator_observations": 84, "lowering_safety_lane_kills": 2, "mutants": 5, "programs": 42, "rejected_fixtures": 13, "semantic_mutant_lane_kills": 8, "timing_samples": 6, "wasm_calls": 58, "wide_host_controls": 18}` |

## Style and integration remainder

The offline style finding is confirmed and remains an integration dependency.
The current branch intentionally retains the shared context tooling; the
coordinator assigns fitting to `perch-cap`, and merging or borrowing another
worktree's implementation is outside this executor's authorization. Nonlocal
ByteOutput context and manifest-wide composition partitioning also belong to
the coordinator's Perch integration. This is not a disputed finding or a style
pass. No code is reshaped solely to fit the judge, and no cap, coverage or
quality threshold is weakened.

| Offline whole-manifest preflight | Before | After |
| --- | ---: | ---: |
| Groups | 21 | 21 |
| Structural blockers | 605 | 626 |
| Truncated contexts | 594 | 615 |
| Unavailable compositions | 11 | 11 |
| Supporting-role exemptions unavailable | 705 | 724 |
| Provider requests | 0 | 0 |

Counts repeat shared declarations across groups. Both commands exit 3 and report
current source freshness. The [offline evidence](../../tests/compiler-closures/receipts/review-r1-style.json)
records both input snapshots, parser/rubric identities, every group's context
counts and the full raw-receipt hashes. Closure-types has 14 truncated contexts,
closure-checking has 31 plus its unavailable composition, closure-lowering has
15, and constructor visibility has one. Closure-checking is 72,998/48,000 bytes
after repair. Seven global compositions still contain unresolved nonlocal
imports. Compression/Maximally big brain, Delight, Memetic identity, Anticipation,
Payoff and composition have no live ratings or distributions; all remain
unqualified. Potential profundity/Galaxy brain remains unjudged.

The smallest honest composition repair requires a shared manifest/tool policy
for selecting bounded collaborating declaration families with explicit imported
interfaces. Splitting file lists alone loses the referenced checking/evaluation
law family; including its full closure recreates the over-limit composition.
The coordinator must preserve every declaration and composition obligation while
partitioning captures, partial application and closure evaluation, then rerun
offline preflight before any live qualification claim. `perch-cap`'s names-only
tier addresses fitting; it does not itself establish complete contexts or solve
the 48,000-byte composition limit. Current tasks and thresholds remain intact.

The existing coordinator remainder is unchanged: serial nest/modules/descent
integration, the D24 request Default, generics' nineteen blocked chooser calls,
shared receipt/census refresh, and live semantic/law/style qualification.
Under D26, function-field is Checked in the catalog with enum emission still
refused; closure-parameter remains Unsupported until lambda-match is modeled;
closure-apply is Checked with generic higher-order support and otherwise genuine
Unsupported. `suffix-cont-lambda-let` and `letop-lambda-dead2` become Checked when
matrix support is sound, otherwise Unsupported. Seed values never move.
No merge, rebase, push, provider call, `.env` access or other-worktree mutation
occurred. All new scratch/build products are under ignored `.local/`.
