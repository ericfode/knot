# Generics precheck round 6 — deterministic gate results

Executed `npm run -s gates` on committed implementation `97eb180e`, with
`BEND_NO_TELEMETRY=1`, `KNOT_GATE_TIMEOUT_SCALE=4`, four workers and a
1,800-second limit per gate. **Exit 0: all 21 gates passed.** The runner started
at 2026-09-30T01:02:00.031908+00:00; total wall time was 566.744248
seconds. Generics took 317.829750 seconds.

The supervisor recorded 38 host-load samples, 15 seconds apart,
from before export until the command completed. The observed one-minute load
range was 21.242188–40.019043.
This is an observed under-load pass, not a controlled speedup measurement.
The supervisor's inclusive wall time was 567.026836 seconds.

| Gate | Status / exit | Exact counts |
| --- | --- | --- |
| frontend | passed / 0 | `{"boundaries": 24, "fixtures": 14, "lane_observations": 28, "mutants": 4}` |
| checker | passed / 0 | `{"bound_observations": 16, "bounds": 2, "budgets": 10, "fixtures": 49, "lane_observations": 98, "mutants": 7}` |
| structural | passed / 0 | `{"bounds": 4, "fixtures": 16, "lane_observations": 64, "mutants": 7}` |
| fields | passed / 0 | `{"bound_observations": 12, "bounds": 2, "budgets": 36, "fixtures": 40, "host_boundaries": 6, "lane_observations": 240, "mutants": 9}` |
| wasm | passed / 0 | `{"boundaries": 44, "execution_lanes": 2, "fixtures": 25, "mutants": 7, "reference_calls": 90, "rejects": 64}` |
| wasm-trust | passed / 0 | `{"entries": 3, "proof_holes": 0}` |
| fields-trust | passed / 0 | `{"entries": 4, "proof_holes": 0}` |
| structural-trust | passed / 0 | `{"entries": 2, "proof_holes": 0}` |
| owned-store | passed / 0 | `{"cases": 3532, "execution_lanes": 2, "literal_witnesses": 15, "mutants": 6}` |
| flat-store | passed / 0 | `{"bun": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}, "mutants": 9, "native": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}}` |
| recursion | passed / 0 | `{"fixtures": 19, "mutants": 3}` |
| fields-wasm | passed / 0 | `{"boundaries": 30, "fixtures": 8, "mutants": 4}` |
| census | passed / 0 | `{"classes": 41, "declarations": 732, "files": 47}` |
| perch-context | passed / 0 | `{"fixtures": 33, "mutants": 8}` |
| lint:verify | passed / 0 | `{"law_rules": 8, "tests": 168}` |
| bootstrap | passed / 0 | `{"corpus": 924, "mutants": 54, "reached": 2, "stages": 8}` |
| classification | passed / 0 | `{"fixtures": 17, "mutants": 7}` |
| io-host | passed / 0 | `{"cli_runs": 6, "conformance_runs": 86, "errno": [2, 9, 20, 21, 22, 92], "fixtures": 20, "host_boundaries": 22, "mutants": 6, "review": {"empty_write": 4, "mutants": 3, "oracle_controls": 14, "secret_paths": 21, "seed_runs": 12}, "seed_fixtures": 40, "seed_runs": 109, "stress": {"left_binds": 100000, "right_binds": 100000}}` |
| io-abi-2 | passed / 0 | `{"case_mode": "insensitive", "fixtures": 43, "host_boundaries": 25, "mutants": 5, "mutants_killed": 5, "parity": 153, "read_observations": 21, "reference_observations": 64, "seed_exhausted": 2, "seed_observations": 61}` |
| selfhost | passed / 0 | `{"blocked": 63, "cases": 65, "d4_gaps": 5, "judge_mutants": 20, "mutants": 3, "passed": 2}` |
| generics | passed / 0 | `{"fixtures": 148, "mutants": 22}` |

## Owned generics coverage

The original 148 fixture requirements and all 17 prior mutants are unchanged.
The added replay contains 13 probes and controls. The gate now kills 22 mutants
in both lanes (44 lane kills), with 16 additional witness kills. All seven
complete proof entries print `All terms check.`; three new laws cover the order
check's guards and zero budget. Their general traversal-refinement obligation
remains open under D21.

```json
{
  "abi_arity_observations": 10,
  "abi_module_probes": 8,
  "additional_mutant_witness_kills": 16,
  "agreed_fixtures": 41,
  "blocked_fixtures": 0,
  "byte_identical_modules": 41,
  "check_observations": 296,
  "compile_observations": 296,
  "evaluator_agreements": 342,
  "execution_lanes": 2,
  "fixtures": 148,
  "host_refusals": 4,
  "mutant_lane_kills": 44,
  "mutants": 22,
  "negative_phase_observations": 642,
  "precheck_byte_identical_modules": 3,
  "precheck_evaluator_agreements": 6,
  "precheck_fixtures": 13,
  "precheck_lane_observations": 104,
  "precheck_preserved_artifacts": 20,
  "precheck_seed_check_observations": 13,
  "precheck_seed_parse_observations": 13,
  "precheck_seed_runs": 3,
  "precheck_wasm_agreements": 6,
  "preserved_artifacts": 214,
  "proof_entries": 7,
  "rejected_fixtures": 62,
  "seed_calls": 226,
  "seed_invalid": 62,
  "seed_valid": 86,
  "unsupported_fixtures": 45,
  "wasm_agreements": 342
}
```

All 248 receipt input hashes match the working tree. All
3204 exported snapshot entries still matched before the owned receipt
refresh. Only the normalized owned generics receipt was copied back. Shared
receipts remain with the coordinator. The runner regenerated 89 artifacts:
64 identical, 9 volatile-only and 16 semantic. No raw runner summary is committed.

| Evidence | SHA-256 |
| --- | --- |
| Normalized summary, canonical sorted JSON with two-space indentation and LF | `f0137494e3776adf867d3c70e46f8527ebbbf43e8f013f48abce92f747b0e025` |
| Exported snapshot | `d8878e657f64db776bb1e6430c04298442b9c65616037b87a75517c2bda38b99` |
| Frozen dependencies | `39d56207556fdd957f299f4aa5999f4dbd8b33785ab0fd3901db68e7f3b6387d` |
| Owned normalized generics receipt | `6d2928489bda45127e8fdc26f87ed62ff2cc276ba991a6475f951f66813412b2` |

Raw logs and summary remain in ignored `.local/gates/run-d3e64res/`;
load samples and the supervisor's measurement remain in ignored
`.local/generics/precheck-6/`. The maintained [owned receipt](receipts/generics.json)
contains the new replay's seed observations, four compiler phases per lane,
module comparisons and mutation evidence. See [PRECHECKS.md](PRECHECKS.md) for
the exact six repaired and six disputed supplied condition fingerprints.

## Review limits and remaining integration

C1 was freshly run on `97eb180e` against `41447157`: exit 0 and zero new executor
conditions. Its seven executed rules include lane-build and the six language
comparisons. The result is **partial**: helper-divergence has no declared helper
lanes, and incomplete-repair has no manifest d4_targets. Reference-crash and
roundtrip are not applicable without the VM codec. This is not an all-rule
pre-review pass; the supplied condition dispositions are independently replayed
in the owned gate.

Offline style preflight: 27 bounded groups,
1242 units, 47 files,
27 available compositions,
zero truncated units, zero structural blockers and zero provider requests.
Compression, Delight, memetic identity, Anticipation and Payoff remain unreviewed;
no numeric style rating or automatic style pass is claimed. The final census
has 47 files, 732 declarations and 41 classes; its tests pass 75/75, and the
frozen frontend definition count remains 48.

Coordinator actions: apply closures D26 integration pins via
[MERGE-WITH-CLOSURES.md](MERGE-WITH-CLOSURES.md), resolve the existing
[RULINGS.md](RULINGS.md) and [BOUNDARY-PINS.md](BOUNDARY-PINS.md) proposals,
refresh shared receipts after integration, and perform authorized live Perch.
No merge, rebase, push, provider call or conditions-ledger edit occurred here.
The inherited monomorphic checker pattern-order residual and cell-valued Wasm
host export boundary remain with their respective owners. General D21
application/parser and traversal obligations remain explicit.
