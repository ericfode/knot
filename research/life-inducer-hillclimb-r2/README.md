# Thirty-trial Life inducer hill climb

Status: stopped for the user’s helper-policy revision after **15 completed
trajectories and 45 rounds, with zero full passes**. Seven requested Astra low
and eight requested Sol xhigh. Forty-two rounds passed behavior; two exhausted
compiler repair and one failed behavior. Forty-one rounds had clean source
review. Fifteen of the original 30 author trajectories remain unstarted.

[The saved results](interrupted-results.json) and [independent audit](interrupted-audit.json)
retain all observed evidence. The audit reports no discrepancies, but explicitly
does not claim a complete 30-trial experiment. [User interruption](user-policy-interruption.json)
stopped dispatch while the three active trajectories finished. The revised
[helper contribution review](../life-helper-review/) re-evaluates saved sources
separately; it does not rewrite this experiment’s outcomes.

This campaign searches for an inducer that helps a fresh author satisfy the
current Perch policy within three revision rounds. The original allocation planned 15 trajectories with
GPT-6 Astra at low effort and 15 with GPT-5.6 Sol at xhigh. Each trajectory has
its own initial context and feedback history. The author CLI records requested
settings; it does not report resolved model or effort identifiers.

Main was rebased through `f1a4364cefa3028f5beb500945fa268422c4d055` before the
campaign. The complete R2 inputs were checkpointed at `39bef90` and are checked
against [the input lock](input-lock.json) before calls and evaluations. The
historical Life sources and receipts remain byte-identical to the pre-rebase
checkpoint. Main's other worktree was not changed.

## Design and acceptance

- [Protocol](PROTOCOL.md): ten initial search trajectories, ten adaptive
  trajectories, then ten held-out trajectories after selection is frozen.
- [Availability amendment](availability-amendment.json): GPT-6 Sol was rejected
  by the account; the available GPT-5.6 Sol route is used in this fresh run.
  The aborted startup remains in [the original directory](../life-inducer-hillclimb/).
- [Stimulus generator](stimuli.py): deterministic mutations of the linked chat's
  decoded inducer, using the copied generator from `bend-tests/sigil/inducers`.
- [Author transport](transport.py): fresh, ephemeral CLI contexts, identical
  common material, no tools, immutable prompts/responses/settings/usage.
- [Independent gates](gate.py) and [law packet](LAW_REVIEW.md): the unchanged
  Life oracle and runtime checks, source review, and all current v3 style targets.

A full pass requires every gate. Correct output or a larger fraction of style
assessments above target is insufficient. Critical or uncertain functions must
reach the Galaxy-brain requirement, and critical or uncertain declarations must
also meet Anticipation and Payoff. Below-target and uncertain ratings remain
distinct in the raw receipts.

The old six-round result used a different style policy and Astra at max effort.
It cannot establish a speedup for this campaign. Fresh original-inducer and
no-inducer controls use this campaign's exact models, rubric and three-round cap.
The held-out samples are small and support descriptive comparisons only.

## Evidence and reproduction

The driver writes immutable assignments, source snapshots, compiler diagnostics,
full-board behavior receipts, semantic/style distributions and model usage under
`trials/Txxx/`. Review paths contain neutral slot identifiers. Exact matching
style reuse is confined to a trajectory; no judge result is shared between
fresh trajectories. Account-backed author dollar cost is unavailable.

The [preflight evidence](../life-inducer-hillclimb/preflight/) contains the 60-test
Perch configuration verification, offline harness checks and independent good,
identity, extinction and one-step behavior controls. The mutants compile but
fail the behavioral oracle. Finite passing observations do not prove universal
Life correctness, GPU support or program runtime improvements.

Run `python3 research/life-inducer-hillclimb-r2/run.py --workers 3` only against
the locked inputs. Existing completed receipts are reused by exact identity;
an unavailable run is preserved and stops dispatch instead of silently retrying.
`progress.jsonl` records scheduling and round completion. The interrupted audit and results above index every completed trajectory.
Only wave 1 completed selection; wave 2 was interrupted and held-out wave 3
never started. Do not resume this old-policy driver after the user’s revision.
