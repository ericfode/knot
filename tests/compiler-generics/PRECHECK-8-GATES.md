# Generics precheck round 8 — deterministic acceptance

Executed `npm run -s gates` on committed implementation `01ab7834a4a45d6ca57a2abd67fe5e9b6817845b`.
**Exit 0: all 21 gates passed.** Original frozen sources, source-language
expectations, values, laws and required semantic controls remain unchanged.
The nine additive controls were seed-frozen separately in `3ed1df52`.

Environment: `BEND_NO_TELEMETRY=1`, Bend 2.0.29 (`574b6d3`), Bun 1.3.14,
Node 22.22.3, four workers, timeout scale 4 and the unchanged 1,800-second
per-gate limit. No timeout fired.
The runner started at `2026-09-30T03:48:32.016750+00:00` UTC and measured
**649.917790 seconds** for the suite. The supervisor measured
660.327356 seconds including invocation overhead.
44 load samples at 15-second intervals span one-minute load
20.488770–41.170410; generics measured 447.273152 seconds.
These are measured completion times under load, not a controlled speed
comparison. The corrected run began while the first run finished generics;
their exported source/build trees and supervision records are separate.

| Gate | Status / exit | Measured seconds | Exact runner counts |
| --- | --- | ---: | --- |
| frontend | passed / 0 | 102.157990 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed / 0 | 37.365402 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed / 0 | 46.211965 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed / 0 | 92.271048 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed / 0 | 77.028965 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed / 0 | 0.658077 | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed / 0 | 1.246185 | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed / 0 | 0.245847 | `{"entries":2,"proof_holes":0}` |
| owned-store | passed / 0 | 7.737997 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed / 0 | 16.069845 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed / 0 | 115.400039 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed / 0 | 253.044344 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | passed / 0 | 7.746985 | `{"classes":41,"declarations":758,"files":51}` |
| perch-context | passed / 0 | 31.377263 | `{"fixtures":33,"mutants":8}` |
| lint:verify | passed / 0 | 8.466559 | `{"law_rules":8,"tests":168}` |
| bootstrap | passed / 0 | 69.782679 | `{"corpus":975,"mutants":54,"reached":2,"stages":8}` |
| classification | passed / 0 | 4.848035 | `{"fixtures":17,"mutants":7}` |
| io-host | passed / 0 | 16.573675 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | passed / 0 | 109.304831 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | passed / 0 | 242.103036 | `{"blocked":63,"cases":65,"d4_gaps":4,"judge_mutants":20,"mutants":3,"passed":2}` |
| generics | passed / 0 | 447.273152 | `{"fixtures":148,"mutants":37}` |

## Owned coverage and source identity

The gate retains all 148 main fixtures and 36 previous mutants. It kills
37 independently type-correct mutants in both lanes
(74 lane kills), plus 38 additional witness kills.
All 9 complete proof entries print `All terms check.`
The new universal equation states the non-leading-template refusal after
a newline, over arbitrary suffixes, source positions, parsed head and fuel.
It supplements the unchanged original law; D21 general obligations remain
required and open. No parser/checker/compiler soundness theorem is claimed.

```json
{
  "abi_arity_observations": 10,
  "abi_module_probes": 8,
  "additional_mutant_witness_kills": 38,
  "agreed_fixtures": 41,
  "blocked_fixtures": 0,
  "byte_identical_modules": 41,
  "check_observations": 296,
  "compile_observations": 296,
  "evaluator_agreements": 342,
  "execution_lanes": 2,
  "fixtures": 148,
  "host_refusals": 4,
  "mutant_lane_kills": 74,
  "mutants": 37,
  "negative_phase_observations": 642,
  "precheck_boxed_module_validations": 4,
  "precheck_byte_identical_modules": 26,
  "precheck_evaluator_agreements": 52,
  "precheck_fixtures": 60,
  "precheck_lane_observations": 480,
  "precheck_preserved_artifacts": 68,
  "precheck_seed_check_observations": 60,
  "precheck_seed_constructor_observations": 1,
  "precheck_seed_parse_observations": 60,
  "precheck_seed_runs": 27,
  "precheck_wasm_agreements": 48,
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

All 307 owned receipt input hashes match the accepted source.
All 3269 exported snapshot entries matched the worktree
before writing this report and refreshing the owned generics receipt.
Coverage independently recomputes to the recorded counts. No compiler, law,
fixture, mutation or gate code changes after acceptance. Only evidence/docs
and census receipt metadata enter the final checkpoint. Shared receipts
remain coordinator-owned.
Regenerated artifact classifications: `{"identical": 64, "semantic": 16, "volatile-only": 9}`.

| Evidence | SHA-256 |
| --- | --- |
| Canonical normalized summary (sorted two-space JSON and LF) | `004a9b2ca90a54fdebcab08eb1eff830a887312cbaddf3d7abbb8ff87c4cc124` |
| Exported source snapshot | `312dd479efa851da69daa40cd02c8da0ff08fd306a8a6aa7cac5f9f4e69d03b9` |
| Frozen dependencies | `39d56207556fdd957f299f4aa5999f4dbd8b33785ab0fd3901db68e7f3b6387d` |
| Normalized owned generics receipt | `435831597720f1a525c8114304f732c4316f041f22bf96b419b3b52762a214eb` |
| Offline preflight raw receipt | `6e75fb4cfb5f56fd0c567b0a5f669bf8341dd57916efd9c2de1c35d1a9f7b902` |
| C1 raw report | `28ae9ab7c75425c6f94935e66249628a8fb761cf7e9862d1ad4428cc41ad1096` |
| `src/parse.bend` | `46cbf786b07603d7a65be14c136f23dea904d45fb298869245b877127ddaca59` |
| `src/parse-layout-LAWS.bend` | `2548105d6fc5f8e1baed2f77014487d0accec5bd96b13116344344dbf1fa2077` |
| `src/parse-layout-PROOF.bend` | `b9522393d172eafa574f7c20b572e53d02073ea1a39e8c757d6db27ef806ce4d` |
| `tests/compiler-classification/check.py` | `0d4b8c457f352984c4ba787ab60dec7f9bb333190aa12e012e1adbc70c32a80f` |

Raw accepted summary/logs remain in ignored `.local/gates/run-t3023ark/`.
Source verification, measurements, baseline/focused observations, C1 and
offline preflight remain in `.local/generics/precheck-8/`. No raw runner
summary with absolute worktree paths is committed.

The initial offline preflight preceded the final precheck task-document edit.
Source-hash verification refused its reuse; a fresh offline preflight matches
every recorded source/task input. Both receipts and the initial verification
failure remain in ignored scratch. No provider request was made.

## Preserved first-run failure

The first full run on `b09e0a99cf391c6ac33ba5dce6414ff244970284` exited 1:
20 gates passed and classification failed. Suite time: 916.644314 seconds.
The classifier refused the stale `nonleading-template` textual mutation
anchor. `01ab7834` changes only its anchor to the normalized guard, retaining
the same False replacement, original inline witness, seed observation,
expected Invalid diagnostic, wrong Unsupported diagnostic and seven-mutant
requirement. Focused classification passes 17 cases and seven type-correct
mutants on nine witnesses. The final complete rerun above qualifies it.
Failed export/logs remain in ignored `.local/gates/run-mdsy9j8l/`.

| First-run gate | Status / exit | Measured seconds |
| --- | --- | ---: |
| frontend | passed / 0 | 179.634942 |
| checker | passed / 0 | 60.490298 |
| structural | passed / 0 | 77.000108 |
| fields | passed / 0 | 166.358511 |
| wasm | passed / 0 | 132.729819 |
| wasm-trust | passed / 0 | 1.277314 |
| fields-trust | passed / 0 | 1.321544 |
| structural-trust | passed / 0 | 0.521738 |
| owned-store | passed / 0 | 12.780488 |
| flat-store | passed / 0 | 37.193266 |
| recursion | passed / 0 | 159.941696 |
| fields-wasm | passed / 0 | 242.428136 |
| census | passed / 0 | 11.595073 |
| perch-context | passed / 0 | 59.588030 |
| lint:verify | passed / 0 | 11.090239 |
| bootstrap | passed / 0 | 86.581208 |
| classification | failed / 1 | 2.651000 |
| io-host | passed / 0 | 21.077478 |
| io-abi-2 | passed / 0 | 77.064198 |
| selfhost | passed / 0 | 241.864172 |
| generics | passed / 0 | 617.420492 |

## Supplied C1 dispositions and remaining limits

Both supplied non-leading-template conditions are fixed; exact offsets are
98 and 110 in both native and Bun parse/check lanes. The remaining visible
conditions are disputed with concrete prefix, TSV and raw constructor
evidence in [PRECHECK-8.md](PRECHECK-8.md). Frozen expectations and the
condition ledger remain unchanged.

Fresh C1 on `b09e0a99` against campaign base `c0bd08d0` covers 923 programs
and exits 3; it is **partial, not a pre-review pass**. Both fixed fingerprints
are absent. The remaining 26 fingerprints exactly match the prior recorded
round-7 dispute/notice set: ten recognized-prefix offset reports, ten code
alphabet reports, one List renderer report and five minor vocabulary notices.
No new unsound-acceptance, crash or Invalid-demotion condition is reported.
C1 reuses the frozen seed verdicts and cached base lanes (zero new seed
runs); the registered generics gate freshly replays all 60 seed syntax/check
observations, 27 main runs and the raw constructor witness. The compiler
source subtree is unchanged between that C1 head and the accepted final
implementation; the later commit only re-anchors the classifier harness.
C1 retains 130 inherited findings: `{"d4-invalid": 28, "diagnostic-shape": 23, "premature-unsupported": 47, "unsound-accept": 32}`.
Helper-divergence and incomplete-repair are unavailable; codec rules do not
apply. Seven language/build rules run. None of these limits is a soundness
pass or newly repaired work.

Offline preflight has 29 complete groups, 1269 units and
51 files, all compositions available, zero truncations/blockers
and zero provider requests/responses. Compression, Delight, memetic identity,
Anticipation and Payoff each remain unreviewed by instruction. The census has
51 files, 758 declarations and 41 classes; frontend definitions remain 49.
Fresh census tests pass 75/75; census:check is current after the owned receipt
refresh. No new dependency/profile or package ownership change.

Coordinator/other-owner actions remain: D26 closures pin/mutant reconciliation,
existing assertion/diagnostic-spelling/recursion-evidence rulings, shared
receipt refresh, live semantic/style review, main integration and the
historical `690bfc61` trailer exception. The monomorphic reconstruction/
pattern-order analogue and boxed host-export boundary retain their owners.
Selfhost still records two passing and 63 blocked cases; this increment does
not establish the whole-compiler fixpoint. See [MERGE-WITH-CLOSURES.md](MERGE-WITH-CLOSURES.md),
[RULINGS.md](RULINGS.md) and [BOUNDARY-PINS.md](BOUNDARY-PINS.md).
No push, merge, rebase, provider call or other-worktree write occurred.
