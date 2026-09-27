# Independent receipt audit

The auditor is outside the frozen author/gate input list. It reads only and
prints JSON to stdout. It does not import the Python runner, execute a candidate,
rerun behavior, call a provider, edit receipts or modify the original startup
batch. The parent owns saving the report and making any Git checkpoint.

From the repository root:

```sh
python3 research/life-inducer-hillclimb-r2/audit.py
python3 research/life-inducer-hillclimb-r2/audit.py --require-complete
```

Exit status is 0 for valid available evidence, including an explicitly partial
run; 1 for an audit discrepancy; and 2 for valid partial evidence when
`--require-complete` was requested. `final_audit_passed` requires all 30 terminal
trajectories, the final result index, and no discrepancies. An intact experiment
with zero full passes can pass its receipt audit; integrity is not program success.

## Checked evidence

- The input lock equals commit `39bef908c7d7ce572b899c73f3d4f8c04ccedffb`.
  Every locked file is rehashed. Assignments reproduce the fixed 10/10/10 waves,
  deterministic schedule, 15 Astra low / 15 GPT-5.6 Sol xhigh requests, stimulus
  hashes and held-out condition labels. Only R2 observations enter the report.
- Author identity, every retained prompt/schema/event/stderr/response hash,
  immutable attempt receipt, successful response alias and emitted final JSON
  are checked. Prompts are reconstructed from the common packet, exact stimulus,
  that trajectory's prior responses, compiler diagnostics and saved feedback.
  Actual CLI arguments, isolation flags, unique thread IDs, zero tool events and
  emitted usage must agree with their receipts. Missing resolved author-model
  fields are reported as requested-only evidence, never a known server model.
- First and repaired source snapshots must exactly equal the corresponding
  response strings. The submitted source hash, compiler outcomes, one-repair
  bound, no unchanged review and first-full-pass stopping rule are checked.
- Behavior receipts bind the submitted hash and lock. Both compressed and
  decompressed raw hashes are checked. Node and Bun retain 1,537 unique full-board
  observations plus 21 unique composition observations each; native expected
  output retains 28 cases. Aggregate pass/failure counts are recomputed without
  printing the large observation arrays or rerunning the oracle.
- Historical judge inputs are rebuilt in memory using the pinned local Bend
  parser and context constructors. The immutable submitted bytes override the
  mutable neutral review file. Parsed declaration inventories, complete style
  targets, context files, untruncated context and exact state hashes must match.
  Only the common cohort and neutral per-trajectory path are accepted; known
  condition/model labels and the complete inducer are rejected in judged source.
  No provider function is invoked; network access through `fetch` is disabled in
  this local constructor process and review credentials are removed.
  An explicitly rejected style context is retained as a nonpass: its exact
  reconstructed truncation, unavailable diagnostics, `attention` status and
  early gate error must agree, with no later style-policy receipt. It never
  satisfies the untruncated-context acceptance requirement.
- Semantic coverage and the four unchanged finding thresholds are checked.
  Semantic usage and style response rows must observe `jev-1.13.0`. The auditor
  independently reconstructs v3 criticality, conditional Galaxy-brain targets,
  Anticipation/Payoff requirements, probability/status assessments and partial
  selection metrics. JavaScript left-to-right floating addition is reproduced:
  a saved boundary classification is not silently rounded into a better result.
  Explicit predecessor reuse is verified and reused usage is not counted again.
- The best eligible round and both selection waves are recomputed using the
  preregistered lexicographic objective, including failure penalty 4 and incumbent
  tie preference. The held-out winner/hash must match wave 2 and its recorded
  selection event. Acceptance uses ordered selection/trial-start events, author
  receipt timestamps and the pinned runner's sequence: write the selection before
  constructing and dispatching wave 3. Selection-file mtime is reported only as
  nonportable corroboration and cannot fail the audit, since Git checkout or
  archival restoration can reset it. This is local evidence, not external
  timestamp attestation. Frozen source, lock, hash and selection checks remain
  mandatory; rerun those from the preserved experiment checkout after a rebase
  that changes locked files.

## Statistics and limits

Each trajectory retains round source hashes, first-shot/repair outcomes,
behavioral and semantic outcomes, per-axis met/required/status counts,
criticality counts, author calls, usage and timing. Aggregates separate adaptive
search from held-out original/selected/no-inducer conditions and separate model
requests. Per-axis aggregate counts cover all reviewed rounds and are labeled
as such, rather than treated as independent trial successes.

Descriptive failure is right-censored at round 3. The search objective's failure
penalty remains 4; these are different quantities. Author CLI time, compiler
time, outer behavior-command time, review-command time and terminal trajectory
elapsed time are separate. Terminal elapsed time includes interruptions; the
runner's invocation-only duration remains separately labeled. Author billed
cost is unknown. Cached input and reasoning-output token fields are subsets,
not additional tokens to sum into a new total.

Judge usage starts with a fresh copy of that round's semantic invocation usage
exactly once. Only fresh style responses are added; copied predecessor rows
retain their historical usage in raw receipts but do not add it again. Totals
within each statistics group count each round once. Per-condition groups and
`ALL_WITHIN_STAGE` are overlapping views and must not be added to each other.

A live audit takes a census of finalized round and trial receipts. Unfinished
current-round calls are excluded from completed-round totals, so partial totals
are lower bounds. The report explicitly marks missing waves and final results;
it does not claim a 30-trial outcome early. The final audit should run after the
runner stops. Search results are not causal evidence for an inducer effect, and
the small held-out samples support descriptive results only.

Initial live validation found no receipt discrepancies in 10 assigned
trajectories, 6 terminal trajectories, 21 completed rounds and 24 author calls.
No full pass had been observed in that census. All 24 author receipts lacked a
resolved-model field, while review receipts observed `jev-1.13.0`. These counts
are a validation checkpoint, not the final experiment result.

Eleven bounded offline rejection/policy checks passed without changing any
experiment artifact: altered author artifact hash, requested model and invented
resolved-model claim; altered raw behavior hash and count; weakened semantic
threshold; omitted style declaration; changed style context hash and actual
judge; inflated style pass; and critical/noncritical/datatype target controls.
The live partial report also returned exit 2 with `--require-complete`, as
specified. A subsequent validation census covered 8 terminal trajectories and
31 completed-round author calls with no receipt discrepancies.

Portability follow-up: five temporary-fixture controls passed. Moving the
selection mtime before or after author receipt times changes corroboration only;
reordered holdout events, a mismatched selection-event winner and runner hash
drift remain rejected. Three usage controls (zero, one and all six style rows
reused) confirmed semantic usage is counted once and only fresh style usage is
added. These tests changed no experiment source, input or receipt.

The follow-up live census also exposed T018 round 1's legitimate rejection:
the `Tally` datatype exceeded the four-caller context limit. The auditor now
retains that exact early style-gate rejection rather than misclassifying it as
receipt corruption. Reconstructed inputs, hashes and selection metrics remain
checked; `style_passed` remains false and truncated targets are reported.
Three controls confirmed this outcome is retained, while a false style-pass
claim or removal of the explicit truncation rejection is still rejected. The
following live partial audit covered 20 assignments and 12 terminal trajectories
with no receipt discrepancies and correctly returned exit 2.
