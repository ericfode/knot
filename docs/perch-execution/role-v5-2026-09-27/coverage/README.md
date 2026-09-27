# Existing-selection parser coverage repair

Two tooling defects are reproduced and repaired. The written configuration,
rules, rubric, thresholds and invalid source fixtures are unchanged. No live
provider was contacted. This increment does not establish a repository pass.

## Distinct defects

1. **Coverage preceded selection.** The analyzer parsed the full Git tree, then
   the semantic reviewer selected paths and applied ignores. The wrapper gated
   the unfiltered parse count. A valid selected file therefore failed because
   of an unrelated ignored malformed file. `before.json` and
   `regression-before.txt.gz` retain that failure. The repair keeps the full graph
   for context, while command coverage includes the configured selection,
   supplied direct callers/callees, and their transitive explicit imports.
   Malformed required context still blocks, even when ignored as a direct target.
2. **Terminal globstar was not recursive.** Upstream handles `**/`, but treated
   the terminal `**` in `directory/**` as two single-level stars. Thus the
   existing `docs/perch-experiments/**` did not exclude nested experiment files.
   `glob-regression-before.txt.gz.gz` retains the failure after the first repair.
   The second repair makes only terminal `/**` recursive. Tests preserve the
   directory boundary, direct-file distinction, single-star behavior and the
   existing `**/` prefix behavior. No new exclusion was introduced.

Both repairs are in `scripts/perch-throughput-patch.mjs`. Tests are in
`tests/perch-bend-integration.test.mjs`.

## Separate effects on the current corpus

| Offline run | Analyzed files | Directly selected | Required context outside selection | Coverage failures |
| --- | ---: | ---: | ---: | ---: |
| Scope repair only (`after.json.gz`) | 425 | 417 | 6 | 16 |
| Both repairs (`after-both.json.gz`) | 425 | 385 | 6 | 13 |

The scope-only run is at `74d87fd`; the second is at `703034d`, after the parent
checkpointed planning artifacts. `summary.json` verifies that all 425 analyzed
source blobs, their parser-status inventory, and configuration are identical.
The three removed failures are the nested historical repair attempts already
covered by the existing ignore. All 13 unignored compiler-fixture failures
remain. The final offline command still exits 1 for partial parser coverage.

`analysis_coverage` retains the full tree; `parser_coverage` records the command
selection plus required context. Each retains a complete per-file status
inventory and `failed_files`. `parser_diagnostics` remains a 20-entry sample,
now accompanied by `parser_diagnostics_capped`; it cannot be mistaken for the
full failure inventory. A regression fills the sample with successful parse
diagnostics and verifies that later failures remain in `failed_files`.

The unchanged style `--all` selection retains all 16 failures. Both complete
path lists are in `summary.json`; the historical style list remains separately
identified inside `after.json.gz`.

## Verification and handoff

- 27 focused offline tests pass (`focused-tests-final.txt`).
- `npm run lint:verify`: 85 tests plus eight-law wiring pass (`lint-verify.txt`).
- `git diff --check` passes.
- The corpus runs use fixed stub answers solely to verify selection and coverage.
  They provide no semantic findings, taste calibration or correctness evidence.
- Installed adapter profile:
  `language-pack-1.20-v3+knot-bend-1d4fdc1f2d654dd5`.
  `adapter-install-final.txt` and `summary.json` retain its identity.

The baseline locked at `74d87fd` keeps its original parser/context identity.
This repair changes the installed adapter identity and invalidates its affected
semantic analysis caches. Historical live receipts are not rewritten. No paid
semantic rerun or style rerun was made by this sidecar. Parent integration owns
the commit and subsequent live review.
