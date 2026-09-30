# Generics review round 1 — deterministic acceptance

Executed `npm run -s gates` on committed implementation `268bc9ac14ca8805cac37b01ef9585993e855fe5`.
**Exit 0: all 21 gates passed.** The original fixture sources, source-language
expectations, values, laws and mutation controls remain unchanged.
The isolated D7 inventory amendment is frontend definitions 48 → 49,
independently enumerated by the pinned seed and committed separately.

Environment: `BEND_NO_TELEMETRY=1`, Bend 2.0.29 (`574b6d3`), Bun 1.3.14,
Node 22.22.3, four gate workers, timeout scale 4 and the unchanged
1,800-second per-gate limit. No timeout fired.
The runner started at `2026-09-30T03:00:32.993564+00:00` UTC and measured
**754.059979 seconds** for the suite; the supervisor measured
765.344114 seconds including invocation overhead.
Its 51 load samples at 15-second intervals span one-minute load
16.970703–54.464355. Generics measured 478.416677
seconds. These are observed under-load completion times, not a controlled
performance comparison. The corrected invocation began while the first
invocation finished its remaining mutation checks; their scratch builds
were isolated and both supervision records are retained.

| Gate | Status / exit | Measured seconds | Exact runner counts |
| --- | --- | ---: | --- |
| frontend | passed / 0 | 155.694533 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed / 0 | 57.496671 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed / 0 | 73.392741 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed / 0 | 151.414765 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed / 0 | 113.785368 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed / 0 | 0.516441 | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed / 0 | 0.656408 | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed / 0 | 0.474393 | `{"entries":2,"proof_holes":0}` |
| owned-store | passed / 0 | 15.417583 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed / 0 | 30.983795 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed / 0 | 127.310375 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed / 0 | 274.592062 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | passed / 0 | 7.097971 | `{"classes":41,"declarations":756,"files":51}` |
| perch-context | passed / 0 | 42.083465 | `{"fixtures":33,"mutants":8}` |
| lint:verify | passed / 0 | 12.168921 | `{"law_rules":8,"tests":168}` |
| bootstrap | passed / 0 | 85.108136 | `{"corpus":966,"mutants":54,"reached":2,"stages":8}` |
| classification | passed / 0 | 7.366638 | `{"fixtures":17,"mutants":7}` |
| io-host | passed / 0 | 19.253878 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | passed / 0 | 93.367744 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | passed / 0 | 278.187642 | `{"blocked":63,"cases":65,"d4_gaps":4,"judge_mutants":20,"mutants":3,"passed":2}` |
| generics | passed / 0 | 478.416677 | `{"fixtures":148,"mutants":36}` |

## Owned coverage and source identity

The owned gate retains all 148 main fixtures and 25 prior mutants. It now
kills 36 independently type-correct mutants in both lanes
(72 lane kills), with
30 additional witness kills.
All 9 complete proof entries print `All terms check.`
Eight new filled equations cover three variable boundaries, four layout/closer
boundaries and newline exclusion from token glue. They prove their exact
declared boundary observations; they do not discharge D21 general parser,
checker, reconstruction or erasure soundness obligations.

```json
{
  "abi_arity_observations": 10,
  "abi_module_probes": 8,
  "additional_mutant_witness_kills": 30,
  "agreed_fixtures": 41,
  "blocked_fixtures": 0,
  "byte_identical_modules": 41,
  "check_observations": 296,
  "compile_observations": 296,
  "evaluator_agreements": 342,
  "execution_lanes": 2,
  "fixtures": 148,
  "host_refusals": 4,
  "mutant_lane_kills": 72,
  "mutants": 36,
  "negative_phase_observations": 642,
  "precheck_boxed_module_validations": 4,
  "precheck_byte_identical_modules": 25,
  "precheck_evaluator_agreements": 50,
  "precheck_fixtures": 51,
  "precheck_lane_observations": 408,
  "precheck_preserved_artifacts": 52,
  "precheck_seed_check_observations": 51,
  "precheck_seed_constructor_observations": 1,
  "precheck_seed_parse_observations": 51,
  "precheck_seed_runs": 25,
  "precheck_wasm_agreements": 46,
  "preserved_artifacts": 214,
  "proof_entries": 9,
  "rejected_fixtures": 62,
  "seed_calls": 226,
  "seed_invalid": 62,
  "seed_valid": 86,
  "unsupported_fixtures": 45,
  "wasm_agreements": 342
}
```

All 296 owned receipt input hashes match the accepted
source. All 3256 exported snapshot entries matched
the worktree before the owned receipt refresh. No compiler, fixture, law,
mutant or gate code changed after this run. The later checkpoint records this
report, documentation, the normalized owned generics receipt and its census
metadata. Shared receipts remain coordinator-owned.
Regenerated receipt classifications: `{"identical": 64, "semantic": 16, "volatile-only": 9}`.

| Evidence | SHA-256 |
| --- | --- |
| Canonical normalized summary (sorted, two-space JSON and LF) | `1687255b4a2914cbf9f372d76e63e3898eaaa8b14300ab18bab832364010ce80` |
| Exported snapshot | `4ccbed89c7de886e81cb8ee49325a5acf56ec5ce9b611dd9185fd32dfa1d1642` |
| Frozen dependencies | `39d56207556fdd957f299f4aa5999f4dbd8b33785ab0fd3901db68e7f3b6387d` |
| Normalized owned generics receipt | `b09f3c8a6836da629f4cf9352d6fe6165d43f56bdc14aee2b6ea77fd3669bb71` |
| Offline preflight raw receipt | `b19dc92e96eed5d1ee1eb831b2d4a88686ad8ea6439bbecb8425013588074469` |

Raw final logs, summary and export stay in ignored `.local/gates/run-j_ywl6x3/`.
Supervisor measurements, the source verifier and focused outputs stay in
ignored `.local/generics/review-r1/acceptance/` and its parent. No raw gate
summary with absolute paths is committed.

## First full run and diagnostic correction

The earlier full run on `97b4e49a9431a0cd60f22c0a65a5c0c5d191fcf8` exited 1:
20 gates passed and frontend failed. It measured
1266.387968 seconds. The frozen `local-import-malformed`
diagnostic moved from `7:8:2:0` to `12:16:3:4` because declaration-name
layout advanced past the original newline. Commit `268bc9ac` confines that
normalization to `def` and `type`. All 30 original parse-classification
controls and the layout proof passed before the complete rerun above.
Its original failed export remains in ignored `.local/gates/run-kwig6kdi/`.
Earlier stopped/failing focused attempts are also retained. Their causes and
the prevention procedure are recorded in `docs/perch-review-log.md`.

| First-run gate | Status / exit | Measured seconds |
| --- | --- | ---: |
| frontend | failed / 1 | 30.699226 |
| checker | passed / 0 | 87.360127 |
| structural | passed / 0 | 114.623551 |
| fields | passed / 0 | 230.894478 |
| wasm | passed / 0 | 173.793089 |
| wasm-trust | passed / 0 | 1.285277 |
| fields-trust | passed / 0 | 1.353320 |
| structural-trust | passed / 0 | 0.756234 |
| owned-store | passed / 0 | 23.985553 |
| flat-store | passed / 0 | 46.267153 |
| recursion | passed / 0 | 223.347441 |
| fields-wasm | passed / 0 | 472.503971 |
| census | passed / 0 | 13.908292 |
| perch-context | passed / 0 | 84.244792 |
| lint:verify | passed / 0 | 15.093023 |
| bootstrap | passed / 0 | 121.413449 |
| classification | passed / 0 | 9.779650 |
| io-host | passed / 0 | 24.850196 |
| io-abi-2 | passed / 0 | 160.736750 |
| selfhost | passed / 0 | 449.094188 |
| generics | passed / 0 | 882.330060 |

## Review dispositions and unavailable evidence

Both confirmed major findings are fixed, with no dispute. Unannotated
reconstructed matched parents are Invalid in generic books; annotated parents,
ordinary aliases and pattern-field aliases retain inference/checking behavior.
All nine reported seed-valid layouts and both inherited layouts are accepted
in parse, check, evaluator and compilation observations. Required delimiters
and token-adjacency controls retain their original refusals. The documented
Bun 1.3.14 selection preserves the frozen runtime expectation. The historical
`690bfc61` trailer exception remains for the coordinator; history is preserved.

Fresh offline preflight covers 29 complete groups, 1,267 units and 51 files:
all 29 compositions available, zero truncations/blockers and zero provider
requests/responses. The six groups containing materially changed mechanisms
have complete context. The broad frontend-parsing task exceeds its task-byte
limit; the bounded frontend-layout task and all affected generic tasks are
available. No potential-profundity or numeric style rating is inferred from
context coverage. Compression, Delight, memetic identity, Anticipation and
Payoff each remain unreviewed under the no-live-review instruction. The older
`receipts/preflight.json` retains its original limited-cohort meaning.

The current census has 51 compiler files, 756 declarations and 41 classes,
with 49 reachable frontend definitions. Census tool tests freshly pass 75/75;
the accepted receipt metadata is regenerated and checked after the owned
receipt refresh. No package or dependency profile changes.

Coordinator actions remain: D26 closures integration and its losing-pin/mutant
reconciliation; existing assertion, boundary-spelling and recursion-evidence
rulings; shared receipt refresh; live semantic/style review; and the historical
coauthor exception. The pure monomorphic checker reconstruction/pattern-order
analogue and boxed Wasm host-export boundary retain their assigned owners.
See [MERGE-WITH-CLOSURES.md](MERGE-WITH-CLOSURES.md),
[RULINGS.md](RULINGS.md) and [BOUNDARY-PINS.md](BOUNDARY-PINS.md).
Selfhost records two passing and 63 blocked cases; this acceptance does not
establish the whole-compiler fixpoint. D21 general obligations remain open.
No merge, rebase, push, provider call or other-worktree write occurred.
