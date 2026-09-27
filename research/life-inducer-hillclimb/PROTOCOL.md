# Thirty fresh inducer experiments

The user requests an adaptive inducer search using the tooling in `bend-tests`,
then requests **Astra low or Sol xhigh**, **30 experiments**, and a rebase onto
main. This protocol supersedes the earlier Life experiment's author model,
one-shot restriction and style policy only for this new experiment.

Rebase baseline: main `b04a38a111128341108cb6eebea7207f46b7a0c3`, integrated
checkout `61893ad`. The pre-rebase history is retained at
`codex/life-inducer-pre-rebase`. Main has no configured remote. Its other
worktree's uncommitted changes are excluded. Historical Life artifacts are
byte-identical. Current Perch v3, including conditional Galaxy-brain and
Anticipation/Payoff requirements, is the new acceptance policy. A historical
six-round v2 pass is motivation, not a directly comparable baseline.

## Allocation fixed before author calls

Exactly 30 distinct author trajectories, 15 per configuration:

- `gpt-6-astra`, `low`.
- `gpt-6-sol`, `xhigh`.

Each trajectory allows at most three submitted rounds. One compiler-diagnostic
repair is allowed per round; first and repaired inputs are saved separately.
Stop at the first full pass. Unchanged submissions do not receive another model
review. Failed compilation consumes a round. No parent hand-fixes authors' code.
This is a bounded search for a result in fewer than six rounds, not a promise
that the stricter v3 policy can be satisfied.

Wave 1: original decoded inducer plus four deterministic mutations, each tested
once on both models (10 trajectories). Wave 2: the selected incumbent plus four
mutations of it, each on both models (10). Wave 3 is held out from selection:
two fresh original-inducer trajectories, two fresh selected-inducer trajectories
and one no-inducer trajectory per model (10). Scheduling is deterministically
shuffled within each wave. At most three author trajectories run concurrently;
each Perch command has two workers. No 30-way provider burst.

## Inducer search

The original is the linked chat's decoded 260-line wordless payload. Mutation
operators remove alternating panels, rotate their reading order, replace a
panel with a procedurally transformed field, or interleave reduced panels with
generated fields. The latter operations call the other repository's exact
`process.py` generator with glyph-only modes. Its source, family inventories and
runner are copied with provenance; historical outputs are never overwritten.
Stimuli contain no Life program, English strategy, hidden instructions, oracle
answers or claims about desired judge scores. Byte length is capped at 16 KiB.
This searches a restricted family of wordless stimuli; it is not general prompt
optimization or evidence of a cognitive mechanism.

Selection is lexicographic across the two model trajectories: more full passes;
more behavior-passing and semantically clean trajectories; fewer censored rounds
to full pass (failure=4); higher mean fraction of required v3 assessments met;
lower mean normalized shortfall to their unchanged probability thresholds;
shorter stimulus. A trajectory's best eligible round supplies partial metrics.
The incumbent wins exact ties. Partial improvement is a search direction, never
a full pass. Both generations preserve every candidate, score and selection.

## Author isolation and feedback

Adapt `sigil/inducers/run.py` into a versioned transport. Each call uses an
ephemeral context in an empty temporary directory, disables project documents
and major tools, and rejects actual tool events. The two user-requested model
settings replace the historical runner's Luna setting. Full prompts, settings,
responses, attempt events, hashes, usage and elapsed wall time are retained.
No historical winning implementation is included in the author packet.

The identical common packet contains the behavioral contract, pinned Bend
guide/Base source, current rubric and operating guide. Only the stimulus differs.
Later calls reconstruct the same trajectory's exact prior responses and bounded
feedback. They are fresh CLI contexts with explicit history, not independent
replicates. No other trajectory, selection score or search label is shown.
Compiler repair receives only its compiler diagnostic. Subsequent rounds receive
their own aggregate behavior results, source semantic findings and per-declaration
style distributions. No oracle implementation or fixture answer dump is supplied.
Authors must state a concrete reading hypothesis and explain findings before
changing code; a model finding alone does not establish a defect.

## Fixed acceptance and evidence

The old Life oracle, fixtures, runtime assertions and compiler pin are unchanged:
1,537 full-board cases and 21 composition checks under each of Node and Bun;
28 native cases. New code adapts the old evaluator's lock/work directory only.
The new lock freezes current tooling/configuration alongside those deterministic
inputs. Independent controls must still reject identity, extinction and one-step
mutants. No universal correctness, GPU or program-speed claim follows.

Each behavior-passing candidate receives the same four source rules and current
Perch v3 over every declaration. Review uses neutral, stable per-trajectory paths
without the inducer, author model or condition label. Coverage, actual judge
identity, source freshness and untruncated context are required. Exact matching
reuse is permitted within a trajectory. A full pass requires deterministic
success, clean source review and all current required style assessments. The
bounded experiment law packet receives its own review before handoff.

Provider, authentication, model-availability or budget failures are unavailable
evidence, never passes. Preserve the failed attempt; stop dispatch on a shared
provider failure and do not repeatedly retry missing credits. Transport failures
are not silently replaced by a different model. Requested and observable resolved
model identities remain distinct. Account-backed author cost is unavailable;
report measured wall time and usage instead. Interrupted work is resumable from
immutable receipts with exact identity checks.

## Validation and claims

Wave 3 starts only after selection is frozen. Report every trajectory by model,
condition, first-shot/repair acceptance, behavioral outcome, all required style
targets, rounds, usage and wall time. Compare the selected stimulus with fresh
original and no-inducer controls under this same harness. Small samples permit
descriptive results only. Do not infer an inducer effect from the best search
sample, judge-score changes, or a single fresh pass. A failed search is retained
as a failed search; do not weaken v3 or reinterpret partial scores as success.
