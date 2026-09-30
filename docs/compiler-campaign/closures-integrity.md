# Closures: scope and receipt integrity follow-up

All fifteen registered gates pass with exit 0 at source checkpoint `946fe412`,
using the disclosed native clang `-O1` host setting. The 19 generic chooser calls
remain blocked and excluded from agreement. Committed-head precheck adjudication
is recorded below; no live Perch or automatic style qualification is claimed.

This round starts at `35b979bf` on `campaign/closures`. The comparison base
reported by the unchanged precheck tool is `fa31fec0`; its main/tool reference
is `b92b1359`. Earlier implementation, freezes and observations remain in Git.
Repository edits and builds stay in this worktree. No branch merge, rebase,
push, `.env` access, provider call or live Perch review is part of this executor
round. One early runner-control invocation used Python's default OS temporary
directory; the harness removed those test directories. Later commands explicitly
set `TMPDIR` to this worktree's ignored `.local/closures/scratch/` directory.

## Scope repair

The seven pre-existing compiler gate scripts and `scripts/gates/test_runner.py`
are restored byte for byte to the comparison base. `scripts/gates/run.py`
retains only the additive closure gate row and its count extraction. The prior
port of shared clang discovery, retry and timeout behavior is removed from
this branch; the coordinator owns the current shared runner at integration.
Host tool discovery for this executor can use an ignored local PATH wrapper,
and the runner's existing `--timeout` argument. Neither changes source budgets
or frozen assertions.

`census:approve` reports no new permissions. Nine previously approved feature
permissions are retained across three refactored declarations, making the
approval policy additive against the base. They are unused permissions, not
fabricated source observations. `npm run census` regenerates the inventories;
no generated inventory is hand-merged. `census:check` reports 42 compiler files,
598 declaration events and 40 classes.

Twelve selected shared-runner receipt, execution and semantic-mutant controls
pass. The workspace-fixture group is excluded because it reads `.env` files.
The full acceptance gate run follows the receipt repair.

## Frozen expectation dispute

`7932bed417c3f5b4c7d1` concerns the structural `function-field` row. It is an
intentional expectation-first amendment, committed in `61554f7c` before the
closure implementation `a1d68911`. The commit body cites the pinned seed and
its literal `On{}` result; [closures-amendments.md](closures-amendments.md)
records the exact command, retained field span and enum-profile refusal.
The checker now supports that seed-accepted affine function field.

C3 requires a literal `amend:` line in the historical commit body. That marker
is absent, although the seed observation and amendment are explicit. Rewriting
the old commit is outside the executor boundary. Restoring its old Unsupported
catalog expectation would contradict the seed, the capability and the frozen
closure-field controls. This finding is disputed on that evidence; the row,
source and seed observations remain unchanged. Fresh seed replay in native/Bun and the complete structural gate both pass.
The field book prints `On{}` in both seed lanes.

## Receipt repair

All eighteen earlier receipts are retained in `tests/compiler-closures/receipts/history/`.
Their dates, measured times, source hashes, seed observations, runtime results
and failures are unchanged. A structural comparison against `35b979bf` verifies
that only path spelling changed: checkout paths become `$ROOT`, toolchain and
package paths use `.toolchain`/`$BEND_LIB`, and transient gate directories use
`$GATE_RUN`. Historical report and review links now point to those receipts.
No historical hash is rewritten to describe the present source.

The closure harness stops hashing local Markdown that it does not execute.
It retains the accepted source contract, all Bend/proof sources, frozen JSON
and fixture sources, and every host/gate script. `receipt_evidence.py` records
a completed fifteen-gate run only after checking the current closure inputs
against the exported snapshot. Its verification mode rereads the current input
hashes, receipt identity and per-gate closure counts. It never refreshes shared
receipts or implements source-language behavior.

Both changed Python sources parse. The eighteen archival comparisons pass, and
their metadata contains no checkout-specific or transient gate path. This
checkpoint is an evidence-workflow change, not a fresh compiler acceptance.
Independent negative controls confirm that the recorder refuses the old stale
current receipt and a retained failed full-suite run before writing acceptance.

## Host-build control

The first serial full-suite attempt hit the frozen frontend script's 30-second
hang guard while building `src/compile-cli.bend` with the seed's default clang
`-O3`. Checker and structural completed successfully. The executor interrupted
the remaining run after that confirmed host timeout; it is not a complete
suite or an acceptance. Its exact timeout, interruption and runner diagnostics
are retained in `receipts/history/integrity-first-gates.json`.

An ignored local clang wrapper appends `-O1` to native seed build invocations.
The same complete `compile-cli.bend` entry then builds successfully in a measured
21.29416024987586 seconds under the unchanged 30-second guard. The pinned seed
files, frozen scripts/assertions, source resource budgets and program expectations
do not change. The full suite is rerun under this explicit host-build setting;
all native/Bun differential results and Wasm bytes must still agree. This is
correctness evidence with a disclosed C optimization setting, not a speed result
or a claim that the default `-O3` host timeout passed. The coordinator's newer
shared hang guards and standard optimized build remain integration work.

## Fresh acceptance

The accepted command was `BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1
--timeout 1800 --keep-scratch`, with the ignored local clang wrapper in PATH.
It exits **0**: all **15** registered gates pass, each with exit **0**.
[Current gate results](../../tests/compiler-closures/receipts/gates.json) record
that host optimization setting and every exact count. [Current closure evidence](../../tests/compiler-closures/receipts/closures.json)
is regenerated from this run. The evidence validator checks all **172** current
input hashes against both this worktree and the exported snapshot; the receipt
identity and reported closure counts also match. No shared receipt is refreshed.

[Scope evidence](../../tests/compiler-closures/receipts/scope.json) confirms
all compiler source remains at the starting source tree
`8b1007574cb442060b514f2b7e6f8505042eac50`. All **123** original frozen control
files remain byte-identical to `35b979bf`. Seven frozen scripts plus the shared
runner tests match `fa31fec0` byte for byte. Original fixture values, expectations,
laws, proof domains and mutants are preserved.

Every row has status **passed** and exit **0**. Counts overlap; do not sum them.

| Gate | Exact counts |
| --- | --- |
| `frontend` | `{"boundaries": 24, "fixtures": 14, "lane_observations": 28, "mutants": 4}` |
| `checker` | `{"bound_observations": 16, "bounds": 2, "budgets": 10, "fixtures": 49, "lane_observations": 98, "mutants": 7}` |
| `structural` | `{"bounds": 4, "fixtures": 16, "lane_observations": 64, "mutants": 7}` |
| `fields` | `{"bound_observations": 12, "bounds": 2, "budgets": 36, "fixtures": 40, "host_boundaries": 6, "lane_observations": 240, "mutants": 9}` |
| `wasm` | `{"boundaries": 44, "execution_lanes": 2, "fixtures": 25, "mutants": 7, "reference_calls": 90, "rejects": 64}` |
| `wasm-trust` | `{"entries": 3, "proof_holes": 0}` |
| `fields-trust` | `{"entries": 4, "proof_holes": 0}` |
| `structural-trust` | `{"entries": 2, "proof_holes": 0}` |
| `owned-store` | `{"cases": 3532, "execution_lanes": 2, "literal_witnesses": 15, "mutants": 6}` |
| `flat-store` | `{"bun": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}, "mutants": 9, "native": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}}` |
| `recursion` | `{"fixtures": 19, "mutants": 3}` |
| `fields-wasm` | `{"boundaries": 30, "fixtures": 8, "mutants": 4}` |
| `census` | `{"classes": 40, "declarations": 598, "files": 42}` |
| `lint:verify` | `{"law_rules": 8, "tests": 127}` |
| `closures` | `{"agreed_fixtures": 49, "blocked_calls": 19, "blocked_fixtures": 1, "boundaries": 14, "boundary_probes": 14, "byte_identity_checks": 49, "check_observations": 174, "checked_laws": 28, "compile_observations": 174, "evaluator_calls": 578, "fixtures": 87, "frozen_fixtures": 42, "mutant_lane_kills": 10, "mutants": 5, "prechecks": {"byte_identity_checks": 6, "check_observations": 52, "compile_observations": 52, "eval_observations": 46, "host_result_refusals": 2, "mutant_lane_kills": 6, "mutants": 3, "parse_observations": 52, "programs": 26, "wasm_calls": 4}, "proof_entries": 4, "refresh_fixtures": 32, "refresh_phase_observations": 192, "refresh_seed_builds": 64, "refresh_seed_calls": 40, "refresh_seed_checks": 32, "refresh_seed_rejections": 12, "regression_fixtures": 11, "regression_phase_observations": 66, "regression_seed_calls": 8, "regression_seed_rejections": 3, "rejected_fixtures": 37, "rejection_evaluator_observations": 76, "seed_calls": 292, "seed_rejections": 18, "supplemental_probes": 2, "supplemental_seed_calls": 8, "wasm_calls": 578}` |

The closure gate replays all 32 refresh edges: 32 checks, 64 seed native/Bun
builds, 40 seed executions and 192 Knot phase observations. Its 26 precheck
programs add 52 parses, checks and compilations, 46 evaluator observations,
two exact host-result refusals and four Node Wasm calls. All four proof entries
fill 28 laws without holes. The original five mutants retain ten lane kills;
the three added parser mutants retain six lane kills. Host timeouts and other
process failures count as neither source rejection nor semantic mutant kills.

## Fresh dispute evidence

[Disputes](../../tests/compiler-closures/receipts/disputes.json) records fresh
pinned-seed checks and executions, then builds/runs both native and Bun wrappers
without changing either original source. The field book returns `On{}`. The full
function-result book returns `invert`; applying that returned function to `On{}`
returns `Off{}` in both seed lanes. Both Knot evaluator lanes in the full closure
gate retain the documented `HostFailure invoke function-result`, exit 5.

- **C1 `7c0871a3666be44005dc` — disputed:** HostFailure is the explicit result
  ABI refusal in unchanged `src/CONTRACT.json`, not a compiler crash. Source
  `b507406b7c59d76848eda88770afed980dd4a861ba9bbc3a10292b90f6588ef2`
  includes the `invert` body omitted by C1's 240-character display. Parsing,
  checking and building that book succeed; observing its function result refuses.
- **C1 `5a7d3ec9413a356cc1ef` — disputed:** `syntax.Error.Host` stores phase/code
  without a source span. `diagnostic.error` emits the documented three-column
  host diagnostic; the SPEC requires offsets where available. Inventing a source
  span or changing the refusal class would alter the frozen host contract.
- **C3 `7932bed417c3f5b4c7d1` — disputed:** the historical expectation-first
  seed amendment is documented above and freshly validated. Its missing literal
  commit-body marker does not justify restoring an obsolete Unsupported pin.

## Committed-head prechecks

[Committed-head reports](../../tests/compiler-closures/receipts/prechecks.json)
check `b0c8e71db334414fbab969e8db3fa65a2bd3ed99` using the unchanged tool and
registry from main `b92b13595bcbc265b823cb3cfdc38918e35953c9`, with
`--head campaign/closures --only C1,C3,C4 --no-write --json --jobs 2` and the
explicit tool main reference. Its C1/C3/C4 implementations were compared byte
for byte to read-only main during this round. No rule, registry, coordinator
ledger or historical commit is edited to suppress a condition.

The combined command exits **3**, retaining exactly the three executor disputes
above: two C1 conditions and one C3 condition. There are no other executor
conditions. C4 reports **zero executor findings**. The local tool export initially
lacked `scripts/gates/normalize.py`; that module was supplied byte-identically
from the same pinned main reference, then C4 was rerun and exited **0**, still
with zero executor findings. The raw reports, including coordinator conditions,
are preserved rather than relabeled as passes.

This is **not a complete precheck pass**. C1 helper-divergence and incomplete-repair
rules have no declared helper lanes or `d4_targets`. C3 has no declared generators
or ownership manifest. C4's gate-run rule notes that current receipt/report files
were recorded after the accepted run's export. These are unavailable checks,
not clean results. The independent acceptance recorder verifies all 172 executed
closure inputs against that export and HEAD. No executed source, frozen control,
shared gate script or source resource budget changed after the accepted run.
Remaining predicted drift of other gates' shared receipts is coordinator-owned.

## Coordinator and other-increment remainder

The main merge is forbidden to this executor and remains serial coordinator
work: nest → modules → descent-2 → closures → literals-integ → generics → VM.
No merge changed this worktree. Reconcile Scope and imported-constructor visibility,
regenerate merged census/shared receipts, and rerun the standard optimized gates
with the coordinator's newer shared host guards.

All D26 items retain their seed observations and values:

- `structural/function-field`: Checked catalog; default enum compilation still
  refuses constructor fields. The seed prints `On{}`.
- `nest/closure-parameter`: Unsupported parse term-form while lambda-match
  shorthand remains absent, after accepting the arrow parameter; never Invalid.
- `generics/closure-apply`: Checked when generic higher-order apply is supported;
  otherwise Unsupported for the genuine missing capability. Generics must run
  the unchanged 19 blocked `generic-choose-bind` calls.
- `suffix-cont-lambda-let` and `letop-lambda-dead2`: after matrix support, Checked
  if the remaining form soundly checks, otherwise genuine Unsupported. Their
  original seed acceptance/`On{}` observations never become Invalid.

D24 request-Default belongs to nest/core-default/VM. D21's general
capture/application preservation theorem remains required and open in the source
SPEC and LAW_REVIEW; finite agreement and the local laws do not discharge it.
Live semantic/law qualification and Compression, Delight, Memetic identity,
Anticipation, Payoff and composition ratings remain unrun, unqualified and
coordinator-owned. Nothing in this report is an automatic style pass.
