# vm-core review round 1

All four findings from review r0 are fixed. No finding is disputed. The review
base is `d9f04137`; repairs are new commits on `campaign/vm-core`.

## Findings and evidence

1. **D7: self-derived loader expectations — fixed in `04ea967e`.**
   `refusal_expectation` derives the complete host triple and outcome registers
   from the reference codec's verdict and SPEC §11's literal host contract,
   before the VM executes. Both the production host baseline and the traced
   baseline must equal it before mutant jobs are constructed. Mutant jobs use
   that independent expectation. Refused fuzz, scope and limit-word images also
   require exact host output, zero entries and zero effects. For magic refusal
   the fixed triple is exit 5, empty stdout and
   `HostFailure\timage\tmagic\n` on stderr.
   An independently assembled refusal-print mutant produces `--\n` and one
   effect while still reporting that exact stderr and exit. The old baseline
   accepts it and its copied expectation misses it; execution of the new
   baseline and job-building code rejects it. Registered semantic mutant
   `loader-refusal-prints` is killed by both `control:bad-magic` and
   `control:version-2`: two wrong observations, zero crashes. The gate now kills
   139 registered mutants, up from 138.
2. **Unreproducible core plans — fixed in `180b9b7e`.**
   `quantum-action` now spells its String as `[113]`; `unsupported-foreign`
   uses `[110, 101, 118, 101, 114]`. Literal conversion reproduces both images
   byte for byte. Before repair 43 of 45 core plan/image pairs reproduced;
   after repair all 45 do. Every core gate now checks these pairs.
   No committed image or frozen expected outcome changed.
3. **Wrong Bun selected by PATH — addressed in `b7abe28a` and the fresh gate run.**
   The reproduction command in CORE.md prepends `/Users/ericfode/.bun/bin`
   and checks Bun 1.3.14. This run verified Bun 1.3.14 and Node 22.22.3 before
   launch; `io-host` and every other gate passed with frozen assertions intact.
4. **Run-dependent study witnesses — fixed in `b7abe28a`.**
   Study receipts record timeout scale, worker counts, group order, job and
   harness guards, source hashes, and every timed-out or skipped job, including
   those before a later clean kill. Timeout events distinguish `deadline` from
   the existing 1,000,000-print guard. A recording control confirms a timeout
   and skipped job remain recorded when a later group kills the mutant, and
   during heavy survivor replay. Real standalone Wasm controls exercise both
   timeout guards and the skipped-next-job behavior. First-kill attribution
   stays separate from result classification and depends on the guards and
   scheduling of the recorded run.

The probe records and logs are in ignored `.local/vm-core/review-r1/` and
`.local/vm-core/logs/review-r1-*`. Durable evidence is in the registered gate
and [core receipt](receipts/core.json), including 45 plan/image hashes, independent
refusal verdicts and the new mutant, and the [study receipt](receipts/study.json).

## Deterministic gates

```sh
export BEND_NO_TELEMETRY=1
export PATH=/Users/ericfode/.bun/bin:$PATH
export TMPDIR="$PWD/.local/vm-core/review-r1/tmp"
bun --version                     # 1.3.14
node --version                    # v22.22.3
KNOT_GATE_TIMEOUT_SCALE=4 npm run -s gates -- --keep-scratch
npm run -s gates:verify
```

`npm run -s gates` exited 0: **22/22 passed**, measured wall time
1,223.840618 seconds. `--keep-scratch` only retains evidence; the flag changes
no assertion. `npm run -s gates:verify` exited 0: **20 tests passed**.
The retained run is `.local/gates/run-bty7cqrp`; its summary and individual logs
supply these exact per-gate counts. Nested counts and overlapping categories
are reported as recorded, not added into one assertion count.

| Gate | Result | Exact receipt counts |
|---|---|---|
| `frontend` | passed, exit 0 | `{"boundaries": 24, "fixtures": 14, "lane_observations": 28, "mutants": 4}` |
| `checker` | passed, exit 0 | `{"bound_observations": 16, "bounds": 2, "budgets": 10, "fixtures": 49, "lane_observations": 98, "mutants": 7}` |
| `structural` | passed, exit 0 | `{"bounds": 4, "fixtures": 16, "lane_observations": 64, "mutants": 7}` |
| `fields` | passed, exit 0 | `{"bound_observations": 12, "bounds": 2, "budgets": 36, "fixtures": 40, "host_boundaries": 6, "lane_observations": 240, "mutants": 9}` |
| `wasm` | passed, exit 0 | `{"boundaries": 44, "execution_lanes": 2, "fixtures": 25, "mutants": 7, "reference_calls": 90, "rejects": 64}` |
| `wasm-trust` | passed, exit 0 | `{"entries": 3, "proof_holes": 0}` |
| `fields-trust` | passed, exit 0 | `{"entries": 4, "proof_holes": 0}` |
| `structural-trust` | passed, exit 0 | `{"entries": 2, "proof_holes": 0}` |
| `owned-store` | passed, exit 0 | `{"cases": 3532, "execution_lanes": 2, "literal_witnesses": 15, "mutants": 6}` |
| `flat-store` | passed, exit 0 | `{"bun": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}, "mutants": 9, "native": {"installed_boundary_states": 2, "instances": 3534, "lifecycle_checks": 7, "observations": 13621}}` |
| `recursion` | passed, exit 0 | `{"fixtures": 19, "mutants": 3}` |
| `fields-wasm` | passed, exit 0 | `{"boundaries": 30, "fixtures": 8, "mutants": 4}` |
| `census` | passed, exit 0 | `{"classes": 41, "declarations": 437, "files": 30}` |
| `perch-context` | passed, exit 0 | `{"fixtures": 33, "mutants": 8}` |
| `lint:verify` | passed, exit 0 | `{"law_rules": 8, "tests": 168}` |
| `bootstrap` | passed, exit 0 | `{"corpus": 921, "mutants": 54, "reached": 2, "stages": 8}` |
| `classification` | passed, exit 0 | `{"fixtures": 17, "mutants": 6}` |
| `io-host` | passed, exit 0 | `{"cli_runs": 6, "conformance_runs": 86, "errno": [2, 9, 20, 21, 22, 92], "fixtures": 20, "host_boundaries": 22, "mutants": 6, "review": {"empty_write": 4, "mutants": 3, "oracle_controls": 14, "secret_paths": 21, "seed_runs": 12}, "seed_fixtures": 40, "seed_runs": 109, "stress": {"left_binds": 100000, "right_binds": 100000}}` |
| `io-abi-2` | passed, exit 0 | `{"case_mode": "insensitive", "fixtures": 43, "host_boundaries": 25, "mutants": 5, "mutants_killed": 5, "parity": 153, "read_observations": 21, "reference_observations": 64, "seed_exhausted": 2, "seed_observations": 61}` |
| `selfhost` | passed, exit 0 | `{"blocked": 63, "cases": 65, "d4_gaps": 5, "judge_mutants": 20, "mutants": 3, "passed": 2}` |
| `vm-spec` | passed, exit 0 | `{"boundaries": 255, "fixtures": 111, "mutants": 284}` |
| `vm-core` | passed, exit 0 | `{"fixtures": 2, "mutants": 139}` |

For `vm-core`, the runner's generic `fixtures: 2` counts the run and dump
sections; it is not a count of fixture executions. The full gate summary is:

```text
vm-core passed: 111 golden images, 44 Book invocations, 38 fixture runs, 38 dump rows, 5 runs equal to the reference evaluation, 24 seeded rows, a lane of 2768 rows (seed 20260929; 84 run again through the seed), 751 admitted images through both, 10 ceiling runs, 3 memory-end runs, 3 growth runs, 3 small-stack runs, 211 refused and 154 admitted controls, 446 refusals replayed to show that they change no state, 7 describe rows, 24 scope rows and 300 scope images, 13 argument controls, 4440 fuzz images (4094 refused, 346 admitted), 9810 limit-word images (9810 refused, 748 of them at a limit, 0 admitted), 139 killed mutants; vm/receipts/core.json
```

The separate `core_plans` section records 45 independently reproduced pairs.
The fresh core receipt was committed in `e5b9ffcf`; all 109 input hashes match
the working tree. Only the owned core receipt was refreshed.

At gate launch the receipt comparison reported 65 identical, 21 volatile-only
and 4 semantic drifts. One semantic drift is the owned core input update now
committed; the other three are shared spec/bootstrap receipts for coordinator
refresh. These do not change the successful gate results.

## Systematic mutant study

```sh
export BEND_NO_TELEMETRY=1
export PATH=/Users/ericfode/.bun/bin:$PATH
export TMPDIR="$PWD/.local/vm-core/review-r1/tmp"
KNOT_GATE_TIMEOUT_SCALE=2 python3 -B vm/check-core.py --study --heavy --jobs 10
```

The study exited 0 in **3,585 measured seconds**: 993 assembled mutants,
**880 clean wrong observations, 14 hangs, 27 traps and 72 survivors**; no
crashed or unassemblable mutants, no unexplained survivors and no stale
explanations. This is **921/993 detected (92.7%)**. All 993 classifications
and all 72 survivor explanations match the receipt at `02aab74d`; no
expectation or survivor explanation was amended. Heavy replay kills four by
a wrong observation and one by a trap.

The fresh receipt records scale 2, 10 ordinary workers, 3 heavy mutant
workers, the group order, job deadlines and harness guards, and gate/harness
source hashes. Its per-row events sum exactly to **178 Timeout and 42,486
Skipped jobs**: **169 deadline guards and 9 print-count guards**. Two mutants
with a later clean kill retain earlier interruptions. Event count is not a
mutant count.

Exactly one first-kill witness differs from the historical receipt:
`$ctor:1919:i32.sub->i32.add@25` stays `killed`, but moves from
`tags/lane:tags-shape` to `inspection/lane:inspect-u32-snil`. Before that clean
kill, the fresh run records four deadline timeouts, each at 40,000 ms:
`lane:keys-u32-3`, `lane:wide-3-flat`, `lane:tags-shape` and
`lane:display-at-bound`, with 46 following jobs skipped across those groups.
The killed-group counts are keys 259, tags 51 and inspection 161, versus
259/52/160 in the earlier receipt. Review r0's scale-4 run had 260/51/160.
These are guard-dependent first observations, while every result
classification and survivor explanation agrees. The historical receipt did
not record its interruptions; matching the documented scale alone cannot
establish that the earlier jobs had the same opportunity to finish.

## Build, preflight and remaining work

`vm.wat`, `vm.wasm` and `build.json` are unchanged. The gate rebuilt both
production and test modules byte-identically using wat2wasm 1.0.41:

- production: 20,278 bytes,
  sha256 `a8ef5f834612ea408eeda8f82252c9e74cca852af7802e125a717f29ae49f9f9`;
- test: 20,668 bytes,
  sha256 `49b15bbdbe0e7ad3170ce1a03203515a100b9b1f992fc756e32878412c97e011`;
- source: sha256 `96bc6c90683537e30d68134ed3d5eecabb1dd5d79643348028f22595175bcb1a`.

No Bend declaration was authored or changed: offline style preflight is N/A,
zero targets. No provider or live Perch calls were made. Census updates only
refresh hashes; files, imports and approved feature classes were not expanded.

Coordinator-only follow-up: mirror the VM sha into `src/CONTRACT.json`, refresh
`vm/receipts/spec.json` and the two bootstrap receipts, and integrate the VM
track and lockstep removal of the earlier named halting relations. No merge,
rebase or push was performed here.

Existing limits remain recorded in CORE.md: vm-io owns allocating imports and
choice 11's UTF-8 growth ordering; vm-rc owns release and tail release before
allocation (`dup`/`drop` remain empty); the spec owner retains the open scope
scratch limit finding. The 72 systematic survivors retain their explanations,
including two reachable layouts with no gate row. Passing the selfhost gate
means its bounded contract passed: 2 of 65 cases execute and 63 stay explicitly
blocked, not a claim of completed compiler self-hosting.
