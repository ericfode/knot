# Closures refresh: branch verification and integration boundary

This is the historical `0dcc51a0` refresh receipt. Later executor precheck repairs
are recorded in [closures-prechecks.md](closures-prechecks.md). They preserve
this frozen corpus and its observations; this document's source-equality audit
describes the earlier snapshot.

This round starts from `a1d68911` on `campaign/closures`. The 2026-09-29 executor
instruction forbids merges, rebases and writes to other worktrees. Consequently
the refresh prompt's main merge is coordinator work; this round does not claim
integration with main. No merge changed this tree. Current main rules were read
from `docs/COMPILER-CAMPAIGN.md` and `COORDINATOR-STATE.md` in the main checkout.

Read-only Git observations during this audit:

| Ref | Observed commit |
| --- | --- |
| main | `aef68c86abbf50f4acd71c3f2c503ead63c44306` |
| campaign/nest | `f6a19c1b952cc6bb62311347ba50895d8c512685` |
| campaign/generics | `a50dcef26c7e7a1cdd9da7069ba480c307defa61` |

The coordinator state document's branch-tip table predates these refs. These
are snapshots, not claims that another increment is accepted or ready.

## Own increment

`e2a5c6b4` freezes 32 fresh closure edges, independently of Knot output: 20
accepted programs with literal results and 12 rejections. The pinned seed checks
all 32, builds in 64 native/Bun lanes and executes 40 accepted calls. The IO
wrappers observe the original source's Flag result. The subsequent differential
gate compares the checker, independent evaluator and actual Fields Wasm in both
Knot lanes. Capture order, function captures, higher-order domains, shadowing,
staged application, fields, erasure, promotion and negative quantity/type/name
controls are covered. No false acceptance, false Invalid or result discrepancy
was found in these probes; the compiler implementation needs no repair.

The original 42 fixtures, 292 seed calls, supplementary erasure/tail probes,
eleven earlier regressions, 24 law statements/proofs and five semantic mutants
are unchanged. The gate wiring adds coverage; it weakens no expectation.
`src/SPEC.md` and `tests/compiler-closures/LAW_REVIEW.md` now explicitly retain
the general capture/application preservation theorem as an open obligation.
Local equations and finite agreement do not discharge it.

## Decision audit

- **D21:** all 24 original closure laws and proof domains remain unchanged.
  General capture-preserving defunctionalization remains open in both required
  trust/review documents, supported by the laws, finite corpus and mutants.
- **D22/D23/D25:** this monomorphic native profile has no host-effect lowering
  or VM request machine. Book/Program entry effects, inert requests and atomic
  VM stops are obligations of the VM/IO owners; this round claims none of them.
- **D24:** a request Default requires the nest/core-default/VM integration.
  This branch has constructor-only core cases and refuses unimplemented effects.
  Supporting pure closures does not establish request-Default execution.
- **D26:** the known pin changes and adjacent continuation probes are listed
  below. No other owner's pins, source files, mutants or seed observations are
  amended by this executor. Re-freezing and two-seed-lane qualification of the
  merged rules belong to the coordinator, after nest/modules/descent-2.

## D26 items

| Frozen item | Existing pin | Most precise sound merged disposition and evidence |
| --- | --- | --- |
| `compiler-structural/function-field` | Main's historical arrow-field refusal | **Checked catalog**, as already frozen by `61554f7` and documented in `closures-amendments.md`. The unchanged seed source returns On. The default enum backend still refuses constructor fields; Fields lowering is independently qualified. Retain merged-tree type IDs and phase diagnostics. |
| `compiler-nest/closure-parameter` | `Unsupported parse parameter-type` | **Unsupported parse term-form** while its `\{...}` lambda-match shorthand remains unimplemented. The source is seed-accepted (On); this branch accepts the arrow parameter and then refuses the shorthand at `264:265:12:11`. Arrow support alone does not make this book Checked. |
| `compiler-generics/closure-apply` | `Unsupported parse parameter-type`, justified by missing closures | **Checked** when the combined generics/closures tree checks generic higher-order apply, retaining the original On result and calls. Until that prerequisite is implemented, **Unsupported** at its genuine missing capability. This branch still refuses the generic Type parameter at `127:131:6:14`; its monomorphic support cannot discharge this generic fixture. The old missing-closures justification must be removed at integration. |

Two seed-accepted nest continuation fixtures are additional merge probes rather
than contradictory closure-suite pins:

| Nest fixture | Nest's pin | This branch's current refusal | Merge requirement |
| --- | --- | --- | --- |
| `round12/suffix-cont-lambda-let` | `Unsupported parse term-form` | `Unsupported parse match-scrutinees` at `148:149:12:10` | After matrix support, Checked if the tree soundly checks the unreachable continuation row; otherwise Unsupported for its remaining form. Seed acceptance forbids Invalid. |
| `round13/letop-lambda-dead2` | `Unsupported parse term-form` | `Unsupported parse match-scrutinees` at `145:146:12:10` | Same rule; preserve the seed's On observation. |

These diagnostic observations were made with the current Bun-built checker on
unchanged Git-object source copies in this worktree's ignored scratch area.
They are not tests of a merged compiler. The broader nest/literals D26 ledger
belongs to those increments; this refresh changes none of its frozen outcomes.

## Verification

The first scratch run stopped after frontend, checker and structural native
builds exceeded the old 30/45-second process hang guards. Its failure diagnostics
and 16 selected runner-control results are retained in
`tests/compiler-closures/receipts/refresh-host-failures.json`. The branch now
uses main's fourfold host guard, 1,800-second gate ceiling, resolved clang/SDK
and one evidence-retaining clang-discovery retry. Seven hang-guard edits match
observed main byte for byte. Source fuel/depth/allocation budgets and every
frozen assertion are unchanged. The full `.env`-fixture workspace unit group
is outside this executor's no-env boundary; the other 16 runner controls pass.

The first completed full run passed all fourteen behavior/test gates, including
the expanded closure gate, and failed census on five stale gate-source hashes
from the host repair. `refresh-pre-census.json` preserves that failed overall
result. `census:approve` printed a blank summary (`"\n"`) and changed no approved
declarations, feature classes or imports. `census` regenerated only those five
hashes in `inventory/accepted.json`. `census:check` then reports current: 39
compiler files, 581 declarations, 501 unique declarations, 372 definitions and
40 feature classes. The following acceptance run verifies all gates together
after regeneration.

The acceptance command completed with exit 0:

```sh
export BEND_NO_TELEMETRY=1
npm run -s gates -- --jobs 2 --keep-scratch
```

All fifteen registered gates passed. The new
[whole-run receipt](../../tests/compiler-closures/receipts/refresh-gates.json)
retains every normalized result, receipt comparison, the full census inventory
and the first clang-discovery failure. The closure gate retried that host fault
once, then passed; the failed 31.478288-second attempt is not source evidence.
The [closure receipt](../../tests/compiler-closures/receipts/refresh-closures.json)
records the expanded available-capability run. Its 144 input hashes match this
working copy. The
[scope receipt](../../tests/compiler-closures/receipts/refresh-scope.json)
confirms all 99 original compiler/fixture/expectation files remain byte-identical
to `a1d68911`. All existing shared receipts retain their historical bytes.

Exact runner counts follow. Every row has status **passed** and exit code **0**.

| Gate | Counts |
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
| `census` | `{"classes": 40, "declarations": 581, "files": 39}` |
| `lint:verify` | `{"law_rules": 8, "tests": 127}` |
| `closures` | Full dictionary below; the 19 generic chooser calls remain unrun. |

Exact closure counts:

```json
{
  "agreed_fixtures": 49,
  "blocked_calls": 19,
  "blocked_fixtures": 1,
  "boundaries": 14,
  "boundary_probes": 14,
  "byte_identity_checks": 49,
  "check_observations": 174,
  "checked_laws": 24,
  "compile_observations": 174,
  "evaluator_calls": 578,
  "fixtures": 87,
  "frozen_fixtures": 42,
  "mutant_lane_kills": 10,
  "mutants": 5,
  "proof_entries": 3,
  "refresh_fixtures": 32,
  "refresh_phase_observations": 192,
  "refresh_seed_builds": 64,
  "refresh_seed_calls": 40,
  "refresh_seed_checks": 32,
  "refresh_seed_rejections": 12,
  "regression_fixtures": 11,
  "regression_phase_observations": 66,
  "regression_seed_calls": 8,
  "regression_seed_rejections": 3,
  "rejected_fixtures": 37,
  "rejection_evaluator_observations": 76,
  "seed_calls": 292,
  "seed_rejections": 18,
  "supplemental_probes": 2,
  "supplemental_seed_calls": 8,
  "wasm_calls": 578
}
```

The 32 refresh programs comprise 20 accepted results and 12 rejections.
They contribute 192 checker/evaluator/compiler phase observations, in addition
to their 32 seed checks, 64 two-lane build observations and 40 seed executions.
The general preservation proof is open; local equations and finite agreement
remain distinct from that theorem. The blocked fixture and its 19 calls are
reported separately and do not count as agreement or executed coverage.

No provider or live Perch call was made. Conceptual compression, Delight,
Memetic identity, Anticipation and Payoff, and the bounded composition review,
are all unrun and unqualified by this executor. No style pass is claimed.

## Coordinator remainder

Integrate main in the prescribed merge order, reconcile the checker Scope API
and D26 pins, regenerate the census at that integration, rerun the full merged
gate set, and refresh shared receipts. Add generics and run the unchanged 19
blocked `generic-choose-bind` calls. Resolve Perch context limits and run the
live source/law/style review on the merged tree. Preserve the recorded open
proof obligation. None of these coordinator or other-increment items is an
executor-completion gate under the 2026-09-29 instruction.
