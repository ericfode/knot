# Registered gate evidence — gpu-emit

Both `BEND_NO_TELEMETRY=1 npm run -s gates` and `npm run -s gates:verify` exited 0.
All 16 registered gates passed. The wrapper self-test passed 18 tests.
No shared gate receipt was copied back or committed; only this increment's GPU receipts were retained.

| Gate | Exact passing counts |
|---|---|
| frontend | boundaries: 24; fixtures: 14; lane_observations: 28; mutants: 4 |
| checker | bound_observations: 16; bounds: 2; budgets: 10; fixtures: 49; lane_observations: 98; mutants: 7 |
| structural | bounds: 4; fixtures: 16; lane_observations: 64; mutants: 7 |
| fields | bound_observations: 12; bounds: 2; budgets: 36; fixtures: 40; host_boundaries: 6; lane_observations: 240; mutants: 9 |
| wasm | boundaries: 44; execution_lanes: 2; fixtures: 25; mutants: 7; reference_calls: 90; rejects: 64 |
| wasm-trust | entries: 3; proof_holes: 0 |
| fields-trust | entries: 4; proof_holes: 0 |
| structural-trust | entries: 2; proof_holes: 0 |
| owned-store | cases: 3532; execution_lanes: 2; literal_witnesses: 15; mutants: 6 |
| flat-store | bun: {"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621}; mutants: 9; native: {"installed_boundary_states":2,"instances":3534,"lifecycle_checks":7,"observations":13621} |
| recursion | fixtures: 19; mutants: 3 |
| fields-wasm | boundaries: 30; fixtures: 8; mutants: 4 |
| census | classes: 40; declarations: 517; files: 33 |
| lint:verify | law_rules: 8; tests: 127 |
| gpu-2 | fixtures: 35; host_boundaries: 64; mutants: 6 |
| gpu-emit | boundaries: 25; fixtures: 9; mutants: 5; rejects: 3 |

Additional receipt detail: recursion has 114 phase observations and 4 fuel probes; fields-Wasm has 32 reference calls, 50 enum byte comparisons and 5 laws. GPU-2 has 4,464 transitions, 308 snapshots, 7 programs / 29 rounds and 28 laws; its six kills are CPU semantic mutants, not fresh WGSL kills.

New GPU summary: `{"boundaries": 25, "compiler_lanes": 2, "device_calls": 0, "eval_observations": 106, "laws": 13, "mutants_killed": 5, "one_step_replays": 4, "programs": 9, "records_observations": 106, "reference_calls": 53, "suspension_checks": 6, "unsupported_observations": 12, "unsupported_programs": 3, "wasm_observations": 106}`.

Receipt comparison: `{"identical": 65, "semantic": 10, "volatile-only": 10}`. Drift is reported by the runner, not rewritten into shared receipts. Semantic drift includes the new source/hash inventories and newly registered GPU receipt artifacts. Every existing assertion remains unchanged.

Fresh Metal execution is unavailable in this sandbox. The default host invocation returned `HostFailure records real Metal adapter unavailable`. See the README for the coordinator command; prior runtime2 Metal qualification is separate historical evidence.

Offline preflight: 132 declarations / 9 files; 22 truncated contexts plus unavailable composition = 23 structural blockers, exit 3, zero provider requests. Composition is 48,102 / 48,000 bytes with 9 unresolved collaborator references and 27 nonlocal-import references. No style axis is rated or passed.

Sources and exact input hashes: `gpu.json`, `preflight.json`; complete observations: `observations.json.gz`. Raw per-gate completion lines and the wrapper test output are retained beside this file.
