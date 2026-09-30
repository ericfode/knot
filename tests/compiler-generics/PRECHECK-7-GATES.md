# Generics precheck round 7 — deterministic gate results

Executed `npm run -s gates` on committed implementation `a65d5f04`.
`BEND_NO_TELEMETRY=1`, timeout scale 4, four workers and the unchanged
1,800-second per-gate limit. **Exit 0: all 21 gates passed.**
The runner started at `2026-09-30T01:40:13.521622+00:00` (UTC). Measured suite wall time
is **1001.769125 seconds**; the supervisor measured
1002.065288 seconds including invocation overhead.
There are 67 host-load samples at 15-second intervals;
one-minute load ranges from 32.942383 to
61.068848. This is an observed under-load
completion, not a controlled performance comparison. No timeout fired.

| Gate | Status / exit | Measured seconds | Exact runner counts |
| --- | --- | ---: | --- |
| frontend | passed / 0 | 229.212432 | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed / 0 | 71.313719 | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed / 0 | 88.252044 | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed / 0 | 201.858743 | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed / 0 | 170.196952 | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed / 0 | 0.986094 | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed / 0 | 1.581004 | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed / 0 | 0.538899 | `{"entries":2,"proof_holes":0}` |
| owned-store | passed / 0 | 14.765295 | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed / 0 | 34.862870 | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed / 0 | 238.846864 | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed / 0 | 406.485547 | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | passed / 0 | 16.297438 | `{"classes":41,"declarations":738,"files":49}` |
| perch-context | passed / 0 | 56.118785 | `{"fixtures":33,"mutants":8}` |
| lint:verify | passed / 0 | 14.501350 | `{"law_rules":8,"tests":168}` |
| bootstrap | passed / 0 | 105.538217 | `{"corpus":945,"mutants":54,"reached":2,"stages":8}` |
| classification | passed / 0 | 7.510774 | `{"fixtures":17,"mutants":7}` |
| io-host | passed / 0 | 19.513627 | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | passed / 0 | 119.101340 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | passed / 0 | 386.903715 | `{"blocked":63,"cases":65,"d4_gaps":5,"judge_mutants":20,"mutants":3,"passed":2}` |
| generics | passed / 0 | 613.768600 | `{"fixtures":148,"mutants":25}` |

## Owned generics coverage

All original 148 fixture requirements and 22 prior mutants remain unchanged.
The gate now kills 25 independently type-correct mutants in
both lanes (50 lane kills), plus
20 additional witness kills.
All 8 complete proof entries print `All terms check.`
Three new universal equations cover header layout at the stated boundaries;
they do not establish general parser soundness or compiler correctness.
D21 obligations remain required and visible in src/SPEC.md and LAW_REVIEW.md.

```json
{
  "abi_arity_observations": 10,
  "abi_module_probes": 8,
  "additional_mutant_witness_kills": 20,
  "agreed_fixtures": 41,
  "blocked_fixtures": 0,
  "byte_identical_modules": 41,
  "check_observations": 296,
  "compile_observations": 296,
  "evaluator_agreements": 342,
  "execution_lanes": 2,
  "fixtures": 148,
  "host_refusals": 4,
  "mutant_lane_kills": 50,
  "mutants": 25,
  "negative_phase_observations": 642,
  "precheck_boxed_module_validations": 4,
  "precheck_byte_identical_modules": 11,
  "precheck_evaluator_agreements": 22,
  "precheck_fixtures": 32,
  "precheck_lane_observations": 256,
  "precheck_preserved_artifacts": 42,
  "precheck_seed_check_observations": 32,
  "precheck_seed_constructor_observations": 1,
  "precheck_seed_parse_observations": 32,
  "precheck_seed_runs": 11,
  "precheck_wasm_agreements": 18,
  "preserved_artifacts": 214,
  "proof_entries": 8,
  "rejected_fixtures": 62,
  "seed_calls": 226,
  "seed_invalid": 62,
  "seed_valid": 86,
  "unsupported_fixtures": 45,
  "wasm_agreements": 342
}
```

All 272 owned receipt input hashes match the final source.
All 3230 exported snapshot entries matched before the
owned receipt refresh. The later evidence checkpoint changes only this report,
README, PRECHECK-7.md and the normalized owned generics receipt.
Shared receipts remain with the coordinator. No raw runner summary is committed.
Regenerated artifact classifications: `{"identical": 64, "semantic": 16, "volatile-only": 9}`.

| Evidence | SHA-256 |
| --- | --- |
| Canonical normalized summary (sorted, two-space JSON and LF) | `c63f5144315060d3717a54a60f23f1185cdb61f051ade982ad6a919156b7a256` |
| Exported snapshot | `4c5a865a0865aac98358aebd45a7399fa6e6d69318f80e9cac70036baf03a552` |
| Frozen dependencies | `39d56207556fdd957f299f4aa5999f4dbd8b33785ab0fd3901db68e7f3b6387d` |
| Normalized owned generics receipt | `47272e5bcb46f6a47e4d292bc5d3af4e31871e73b5954fca646a31c2bac882dc` |

Raw logs and summary stay in ignored `.local/gates/run-wmcjckvp/`.
Load samples, the supervisor record, focused controls and C1 outputs stay in
ignored `.local/generics/precheck-7/`. The focused run measured 268.490350
seconds. Its initial missing-SDK clang failure is retained; the successful
retry uses the SDK setup already provided by the full runner. This round made
one full-suite invocation, which passed. No compiler or test code changed after it.

## Pre-review outcome and limits

C1 runs on `a65d5f04` against campaign base `c0bd08d0`, over
923 frozen/generated programs. It exits 3, with 26
remaining conditions (one blocking, 18 major and seven minor); it is **not a
pre-review pass**. All six new Invalid demotions in the starting head are gone.
No new unsound-acceptance or crash condition is reported. The starting head
had 38 conditions; the repair removes 12. The supplied header-layout condition
is fixed and the other 12 supplied fingerprints retain the evidence-backed
disputes in [PRECHECK-7.md](PRECHECK-7.md). Frozen expectations and the
condition ledger are unchanged.

| Remaining C1 group | Count | Disposition | Fingerprints |
| --- | ---: | --- | --- |
| minor prefix table coverage | 5 | Five nonblocking documentation notices: existing bare-quantity-field/type-prefix refusals recognize a prefix before the seed error, but the table does not enumerate those codes. Retained for coordinated contract/vocabulary review; no acceptance or Invalid demotion is observed. | `040e6b7dbd5961089b8e`, `2cf3c676b26370652f45`, `8871f7d2677da92c3637`, `aa3372692565233f19ff`, `030e2db315bd4b9f368d` |
| recognized prefix offset | 10 | Disputed: diagnostic spans locate the argument or detached brace after recognition, rather than the recognition boundary. Fixed pins and laws remain required; modules owns the detached-brace vocabulary ruling. | `2479f63e20371fb1bd9e`, `3243ea49e491d4a71e20`, `c98eec3a22494b9f0201`, `47be583c3da6e599c04c`, `c4de74648438ec56de92`, `e7e4004ce37fce303e1b`, `8ce3d10d8fd5af8e2dda`, `8273abdbad9742b4b76c`, `5264f778e94f4ed7cd17`, `a1479dce25d3a23b6d32` |
| TSV code alphabet | 10 | Disputed: expected-: and expected-= are valid non-control TSV field contents; all four fields and exit classes remain correct. | `61d4c9784682a189d345`, `5ddb3eb23c17c9de47b6`, `0f32458d73d3e58df568`, `5fee6563bd061837ffcf`, `00546995d664301756fd`, `269defa1a458be69e47f`, `608406965dc27e23a524`, `36eeabfa0e638156852f`, `18e2562cd65b8c1e20e3`, `d045283ad2e89594a37d` |
| empty List renderer | 1 | Disputed: the seed kernel reports nullary Nil and sugars it as []; the unchanged Knot pin renders the same constructor Nil{}. | `48be3d3057909f734efb` |

C1 separately records 140 inherited findings, present at
the campaign base: `{"d4-invalid": 38, "diagnostic-shape": 23, "premature-unsupported": 47, "unsound-accept": 32}`.
Those are not a soundness pass or newly repaired work. In particular, baseline
Invalid demotions and unsound acceptances remain with their existing owners.
Helper-divergence has no declared helper lanes and incomplete-repair has no
manifest d4_targets. Codec rules are not applicable. Seven language/build
rules ran; this partial pre-review does not qualify unavailable rules.

Offline preflight has 28 bounded groups, 1248 units, 49 files, all 28
compositions available, zero truncations/blockers and zero provider requests.
Compression, Delight, memetic identity, Anticipation and Payoff all remain
unreviewed by instruction. No numeric rating or automatic style pass is claimed.
The current census has 49 files, 738 declarations and 41 classes; the frontend
definition count remains 48. The inherited census test receipt passes 75/75
on these unchanged inventory inputs; current census:check passes freshly.

Coordinator actions: closures D26 integration and losing-pin reconciliation,
the existing assertion/pin and contract-vocabulary rulings, shared receipt
refresh after integration, and live semantic/style Perch. See
[MERGE-WITH-CLOSURES.md](MERGE-WITH-CLOSURES.md), [RULINGS.md](RULINGS.md)
and [BOUNDARY-PINS.md](BOUNDARY-PINS.md). The inherited monomorphic checker
pattern-order residual and boxed Wasm host-export boundary keep their owners.
The selfhost gate still records 2 passing and 63 blocked cases; generics
executor completion does not establish the whole-compiler fixpoint.
No merge, rebase, push, provider call or other-worktree write occurred.
