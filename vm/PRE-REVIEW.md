# vm-model deterministic pre-review repairs

Tested implementation: `6f90c977b5a94464df7408e6e4b79c9d8db882a2`. Baseline: `6e978f19`.

Both supplied executor conditions are confirmed and fixed in `fbc47621`.

| Condition | Repair |
| --- | --- |
| C3 `shared-file-shape`, `bc7e4c3c95f3ebca7c07` | The shared runner and its tests match their pre-guard bytes. The increment diff in `scripts/gates/run.py` retains only its additive VM gate row. Runtime preflight and its controls moved into the owned `vm/run-gates.py` and `vm/test-runtime.py`. |
| C4 `host-path`, `1ef25c2f374414a817db` | The historical review receipt no longer stores local run-directory or summary pointers. Run ordinals identify the observations; all historical results, hashes and measured timings are preserved. The receipt has zero host-path matches. |

`python3 -B vm/run-gates.py` checks PATH against io-host's unchanged Bun pin before invoking `npm run -s gates`, forwarding arguments and the exit status. Its three controls pass, including wrong-version, failed/missing probe, no workspace mutation and forwarding. The shared runner's original 20 tests pass. Direct commands select Bun 1.3.14 and export `BEND_NO_TELEMETRY=1`.

`6f90c977` refreshes two census digests after restoring the runner: `accepted.json`'s registry hash and `selfhost.json`'s dependent input hash. `census:check` passes. Compiler inventory remains 30 files, 437 declarations and 41 feature classes. No feature approval, frozen expectation, accepted law or Bend source changes.

Two consecutive `npm run -s gates` runs exit 0, with all 22 gates passed in each. Measured total times: 444.403394 and 674.417716 seconds. Their complete normalized summaries are identical, and all 90 normalized receipt artifacts match byte for byte. The comparison SHA-256 is `f809e74e4caf261a7f5322f743cb61e4a330d2e97420e521c89ef4d5c48bf77d`. The [portable receipt](receipts/pre-review.json) records exact counts, hashes, proof evidence and condition dispositions.

| Gate | Exact passed coverage |
| --- | --- |
| frontend | `{"boundaries":24,"fixtures":14,"lane_observations":28,"mutants":4}` |
| checker | `{"bound_observations":16,"bounds":2,"budgets":10,"fixtures":49,"lane_observations":98,"mutants":7}` |
| structural | `{"bounds":4,"fixtures":16,"lane_observations":64,"mutants":7}` |
| fields | `{"bound_observations":12,"bounds":2,"budgets":36,"fixtures":40,"host_boundaries":6,"lane_observations":240,"mutants":9}` |
| wasm | `{"boundaries":44,"execution_lanes":2,"fixtures":25,"mutants":7,"reference_calls":90,"rejects":64}` |
| wasm-trust | `{"entries":3,"proof_holes":0}` |
| fields-trust | `{"entries":4,"proof_holes":0}` |
| structural-trust | `{"entries":2,"proof_holes":0}` |
| owned-store | `{"cases":3532,"execution_lanes":2,"literal_witnesses":15,"mutants":6}` |
| flat-store | `{"bun":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621},"mutants":9,"native":{"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}}` |
| recursion | `{"fixtures":19,"mutants":3}` |
| fields-wasm | `{"boundaries":30,"fixtures":8,"mutants":4}` |
| census | `{"classes":41,"declarations":437,"files":30}` |
| perch-context | `{"fixtures":33,"mutants":8}` |
| lint:verify | `{"law_rules":8,"tests":168}` |
| bootstrap | `{"corpus":943,"mutants":54,"reached":2,"stages":8}` |
| classification | `{"fixtures":17,"mutants":6}` |
| io-host | `{"cli_runs":6,"conformance_runs":86,"errno":[2,9,20,21,22,92],"fixtures":20,"host_boundaries":22,"mutants":6,"review":{"empty_write":4,"mutants":3,"oracle_controls":14,"secret_paths":21,"seed_runs":12},"seed_fixtures":40,"seed_runs":109,"stress":{"left_binds":100000,"right_binds":100000}}` |
| io-abi-2 | `{"case_mode":"insensitive","fixtures":43,"host_boundaries":25,"mutants":5,"mutants_killed":5,"parity":153,"read_observations":21,"reference_observations":64,"seed_exhausted":2,"seed_observations":61}` |
| selfhost | `{"blocked":63,"cases":65,"d4_gaps":5,"judge_mutants":20,"mutants":3,"passed":2}` |
| vm-spec | `{"boundaries":255,"fixtures":111,"mutants":284}` |
| vm-model | `{"boundaries":45,"fixtures":6,"mutants":65}` |

The model passes 111 goldens, 44 invocations, 108 fuel controls, 212 refusal controls, 13 argument controls, 165 admitted controls, 107 audited runs and 45 installed-state controls. The soundness sweep covers 65,469 mutations of 111 images. All 49 laws check, all 65 model mutants have execution kills, and the harness mutant is killed. The zero-leak audit stays green. The model receipt matches all 14 source hashes and the frozen boundary-expectation hash; its bytes match the committed receipt.

No new Bend fixtures or model mutants were needed for these two conditions. The existing request mutants (`eager-effect`, `let-performs-request`, `default-refused`) remain execution-killed. The native full-frame Enter control retains its debit; complete store/output/pending-control comparisons and Book description preservation remain covered by the 45 controls and their checked laws.

All 22 repository proof entries have `All terms check.` evidence. `packages/symbols/PROOF.bend` has a main value, so its proof check uses `--check-only`. The initial direct VM proof attempt was inconclusive at an incorrectly short 300-second hang guard; the registered model gate checks all 49 laws under its documented 1,800-second base guard. No proof was changed.

The C3/C4 check on the tested implementation exits 0 and neither supplied fingerprint remains. C4 has no unavailable rule at that checkpoint. C3 cannot run generator/scope checks because its coordinator manifest declares neither generators nor owns. Two minors remain there: GATES.md deletions arise from literal conflict markers in the synthetic effective base, while GATES.md is unchanged in this repair; the boundary hash is recorded provenance, and the evidence capture independently verifies it against the literal frozen file.

The evidence tree's C3/C4 check also exits 0. It labels the two standalone review receipts as orphans; these summarize historical executions rather than promise regeneration by a registered gate. Its gate-freshness rule is unavailable because the finished runs precede only `vm/PRE-REVIEW.md` and `vm/receipts/pre-review.json`. The tested implementation, expectations and model receipt are unchanged. These metadata limits are recorded, without claiming an automatic precheck pass.

The first full run is retained as failure evidence: census alone failed on the stale runner digest; all other gates, including vm-model, passed. The two corrected acceptance runs supersede it.

Offline Perch is unchanged: this repair has zero changed Bend files. Prior bounded preflight covers 10 groups with zero structural blockers; the combined five-file preflight retains 113 blockers. Live ratings remain unavailable and no semantic or automatic style pass is claimed. No provider call was made.

Frontend/modules reconciliation owns seed-valid empty datatypes. The coordinator owns live Perch, VM integration and the three shared semantic receipt updates (bootstrap progress/reference and vm-spec). Those receipts are preserved here. Finite controls and checked state laws do not establish universal compiler or validator correctness.
