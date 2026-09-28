# Registered gate results

All 15 registered gates exited 0 on the final implementation. `gates:verify` passed 18/18 controls. Categories overlap and must not be added into a single assertion count.

| Gate | Exact passing counts |
|---|---|
| frontend | 24 boundaries; 14 fixtures; 28 lane observations; 4 mutants |
| checker | 16 bound observations; 2 bounds; 10 budgets; 49 fixtures; 98 lane observations; 7 mutants |
| structural | 4 bounds; 16 fixtures; 64 lane observations; 7 mutants |
| fields | 12 bound observations; 2 bounds; 36 budgets; 40 fixtures; 6 host boundaries; 240 lane observations; 9 mutants |
| wasm | 44 boundaries; 2 execution lanes; 25 fixtures; 7 mutants; 90 reference calls; 64 rejects |
| wasm-trust | 3 entries; 0 proof holes |
| fields-trust | 4 entries; 0 proof holes |
| structural-trust | 2 entries; 0 proof holes |
| owned-store | 3,532 cases; 2 execution lanes; 15 literal witnesses; 6 mutants |
| flat-store | bun: 2 installed boundary states, 3,534 instances, 7 lifecycle checks, 13,621 observations; 9 mutants; native: 2 installed boundary states, 3,534 instances, 7 lifecycle checks, 13,621 observations |
| recursion | 19 fixtures; 3 mutants |
| fields-wasm | 30 boundaries; 8 fixtures; 4 mutants |
| census | 40 classes; 425 declarations; 30 files |
| lint:verify | 8 law rules; 127 tests |
| gpu-2 | 35 fixtures; 64 host boundaries; 6 mutants |

gpu-2 additionally checks 28 filled laws, 4,464 transitions / 308 complete snapshots, seven programs / 29 complete round snapshots across independent Python and both seed lanes. Its six mutants typecheck and fail their named laws and unchanged observations. Shader validation separately constructs 11 variants / 33 pipelines; ten device mutant kills remain unrun.

Receipt classifications: `{"identical": 63, "semantic": 3, "volatile-only": 17}`.

All three semantic differences are new gpu-2 outputs absent from the Git
baseline. No existing gate receipt has semantic drift.

Semantic receipt drift: `research/adaptive-tasks/runtime2/receipts/cpu.json`; changed fields `["/"]`. This does not change a gate assertion.

Semantic receipt drift: `research/adaptive-tasks/runtime2/receipts/observations.txt.gz`; changed fields `["/"]`. This does not change a gate assertion.

Semantic receipt drift: `research/adaptive-tasks/runtime2/receipts/programs.txt`; changed fields `["/"]`. This does not change a gate assertion.

The invoking worktree was not modified by the gate runner. Shared receipts remain with the coordinator. The compiler census is unchanged: 30 files, 425 declarations, 40 feature classes; no source census approval was needed.

Fresh legacy replay: 87 tracked adaptive-task files byte-identical to d14418b; runtime-1 16 cases / 62 commands / 186 phase observations / 8 laws / 7 CPU mutants; 24 replay-comparison controls; 6 output-hygiene tests. The retained 38-case Metal receipts compare equal. No fresh device replay is claimed.
