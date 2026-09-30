# opt-1 receipt portability repair

This executor round starts from `5854e614`. It addresses all seven reported
executor C4 `host-path` conditions, preserving the completed refresh corpus,
implementation, frozen expectations, laws and mutants.

The historical gate runner normalized checkout prefixes but retained its random
run directory. Those directories belong in ignored local evidence. Committed
receipts retain portable file identities and content hashes instead.

| Receipt | Repair |
| --- | --- |
| `receipts/gates-first.json` | Remove `/run/directory`. |
| `receipts/gates-first.txt` | Point `Summary:` to `$ROOT/tests/compiler-opt/receipts/gates-first.json`. |
| `receipts/gates-review2-first.json` | Remove `/run/directory`. |
| `receipts/gates-review2.json` | Remove `/run/directory` and `/optimizer_receipt/copied_from`; retain the receipt path, SHA-256 and equality evidence. |
| `receipts/gates.json` | Remove `/run/directory`. |
| `receipts/gates.txt` | Point `Summary:` to `$ROOT/tests/compiler-opt/receipts/gates.json`. |
| `receipts/manifest-failure.txt` | Replace the exported-worktree prefix with `$ROOT/` in both failure locations; retain file names and line/column numbers. |

`receipts/c4-portability.json` records every condition fingerprint, the before
and after hashes, and the exact permitted changes. Parsed JSON equality holds
after deleting only the five metadata fields. Text equality holds after only
the four path substitutions. Nine volatile paths are removed. Observations,
statuses (including historical failures), counts, commands, timings, assertion
messages and content hashes remain unchanged. Normalization with an unrelated
checkout root is idempotent.

The audit scans every opt-1 receipt for absolute home/temp paths and random
gate-run paths. It also verifies all 177 optimizer and 80 refresh input hashes
against the current files. The repair changes no frozen input, compiler source,
package source, gate implementation or shared receipt. The prior 32-program
seed refresh and its acceptance evidence remain in `REFRESH-2026-09-29.md`.

## Portable evidence procedure

Keep the gate runner's raw summary, logs and export paths under ignored
`.local/`. When retaining an opt-1 gate summary, omit `run.directory` and
copy-source directories. Retain the normalized gate results, source/dependency
hashes, receipt identities, durations and harness limits. For failure stacks,
map the exported-worktree root to `$ROOT`, preserving the relative file and
position. For a textual summary link, use the committed JSON receipt path.
Before committing, compare JSON/text with the raw evidence allowing only these
metadata changes; scan the retained receipt set for host and random-run paths.
No general path-erasing rewrite of observations is permitted.

## Verification and boundaries

The normalization checkpoint is `795a9dbb`. A fresh
`BEND_NO_TELEMETRY=1 npm run -s gates -- --jobs 1 --timeout 1800` on that committed
head exited zero: all eighteen gates passed in 1419.115490 seconds.
The optimizer gate took 769.161947 seconds. These
measured durations are verification evidence, not a performance comparison.
`receipts/c4-gates.json` retains every exact count, measured duration, normalized
receipt identity and the tested head. Every gate's counts match the prior
refresh result. All 177 optimizer and 80 refresh input hashes also match the
freshly generated receipts. Their outputs remain in ignored runner evidence;
committed optimizer and shared receipts are preserved.

The final portability audit scans 33 receipts with zero remaining host/temp or
random-run paths. Both the audit and `git diff --check` pass. The standalone
wrapper suite passes eighteen tests, including six semantic mutant controls.
Its retained run exports `TMPDIR`, `TMP` and `TEMP` under ignored `.local/`; an
initial standalone run used the host-default temp directory before this
correction. The full gate runner isolated its scratch files under `.local/`
throughout.

Bootstrap passes its existing progress contract: two of eight stages reached,
six blocked, 692 corpus files and nine mutants. Self-hosting remains incomplete.

| Gate | Result | Exact counts |
| --- | --- | --- |
| frontend | passed (exit 0) | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | passed (exit 0) | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | passed (exit 0) | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | passed (exit 0) | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | passed (exit 0) | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | passed (exit 0) | `{"entries":3,"proof_holes":0}` |
| fields-trust | passed (exit 0) | `{"entries":4,"proof_holes":0}` |
| structural-trust | passed (exit 0) | `{"entries":2,"proof_holes":0}` |
| owned-store | passed (exit 0) | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | passed (exit 0) | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | passed (exit 0) | `{"fixtures":19,"mutants":3}` |
| fields-wasm | passed (exit 0) | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| compiler-opt | passed (exit 0) | `{"abi_checks":154,"accepted_programs":66,"boundaries":18,"core_idempotence_checks":148,"core_round_observations":154,"core_verifier_controls_per_lane":43,"corpus_growth_controls":8,"default_enum_byte_checks":50,"direct_pointer_host_calls":0,"execution_lanes":2,"generated_programs":9,"new_fixture_reference_calls":58,"new_fixtures":13,"new_laws":16,"observer_programs":11,"observer_reference_calls":22,"reference_calls":222,"refresh":{"abi_checks":256,"abi_decodes":320,"accepted_programs":32,"core_round_observations":192,"core_signature_checks":64,"evaluator_checks":320,"execution_lanes":2,"false_invalid":0,"native_bun_byte_checks":160,"native_bun_core_checks":96,"seed_reference_calls":64,"seed_rejected_programs":0,"source_programs":32,"tail_position_controls":8,"value_mismatches":0,"wasm_calls":320},"rejected_programs":8,"rejection_lane_observations":16,"review_controls_per_lane":14,"self_tail_module_checks":616,"semantic_mutants":7,"single_pass_abi_checks":462,"single_pass_evaluator_checks":1332,"source_programs":74,"structured_result_observers":22,"unfrozen_off_programs":0,"unoptimized_byte_checks":154}` |
| census | passed (exit 0) | `{"classes":41,"declarations":567,"files":38}` |
| perch-context | passed (exit 0) | `{"fixtures":33,"mutants":8}` |
| lint:verify | passed (exit 0) | `{"law_rules":8,"tests":168}` |
| bootstrap | passed (exit 0) | `{"corpus":692,"mutants":9,"reached":2,"stages":8}` |
| classification | passed (exit 0) | `{"fixtures":17,"mutants":6}` |

No provider/live Perch call is made. Style axes remain unrated. Current-main
integration, D26 shared-pin reconciliation, Default/empty-core support from
other increments, shared receipt refresh and live review remain coordinator
actions as recorded in the refresh report. The executor does not merge, rebase,
push, or change another worktree.
