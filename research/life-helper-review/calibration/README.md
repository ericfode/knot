# Helper-support calibration controls

These fixtures test the experimental `supports_main_idea` question in
[config.json](../config.json). They do not modify `perch-style.json`, historical
scores, author prompts or the frozen R2 acceptance policy. Whole-family review
retains the exact five v3 level arrays: Galaxy-brain level 5 at probability
0.60, and delight, memetic, anticipation and payoff at level 3 with probability
0.60. Declaration support has its own level-3/0.60 target. Both kinds of result
must pass independently; high support cannot supply a missing family pass.

## Expected comparisons, before live review

The human preference supplied by the user is: “Helpers should support the main
thing being Galaxy brain.” The concrete labels below are the assistant's
pre-review operationalization of that preference, not independently collected
human-panel ratings. [expectations.json](expectations.json) records the timestamp,
policy/source hashes, helper targets, expected comparisons and semantic arguments
before any live support call. No source asserts a desired score or labels itself
as a positive/negative example. Present fixtures under neutral identifiers and
keep this expectation metadata out of model review context.

All four fixtures satisfy the same intended Life interface and domain. The
negative examples deliberately impair contribution clarity while preserving the
underlying computation. They are style/support controls, not behavioral mutants.
No family is assumed to meet Galaxy-brain, and no family-score ordering is used
as a calibration expectation. Score every parsed declaration; the comparisons
below select the support observations whose separation is being tested.

| Split | Higher-support fixture / target | Lower-support fixture / target | Expected distinction |
| --- | --- | --- | --- |
| Development: rolling sums | [D01](fixtures/D01.bend.snapshot), `head0` | [D02](fixtures/D02.bend.snapshot), `head0` | A direct zero-or-head match versus the same result passed through alternating ignored-tag projection interfaces |
| Held out: packed bitplanes | [H01](fixtures/H01.bend.snapshot), `Life.eight_winds` | [H02](fixtures/H02.bend.snapshot), `Life.eight_winds` | A visible three-row neighbor layout with its center absent versus a scrambled positional call reconstructed by a separate permutation helper |

For each selected target, the higher fixture is expected to meet support and the
lower fixture not to meet it. D02's added `Boundary.reserve`/`Boundary.transit`
and H02's added `Life.route` are also expected below the support target: in these
programs they add an arbitrary convention without a corresponding useful role.
This is not a blanket claim that projections or permutation adapters are poor
helpers. Their contribution must be assessed in the supplied full program.

## Fixed mechanisms and preserved semantics

D01 is the unchanged T007 round-3 rolling-sum source. D02 changes only boundary
lookup and adds two projections; `horizontal`, `resolve`, `sweep`, `step` and
`evolve` remain byte-identical. Algebraically,
`reserve(value,tag)=value` and `transit(tag,value)=value`. Consequently the empty
case remains zero and the nonempty case remains the original head. The tags have
no state or effect. No error path, hidden mutation or new Life rule is introduced.

H01 is the unchanged T006 round-3 packed-row source. H02 changes the neighbor
adapter and adds `Life.route`; the packing, bitplane counter, row sweep, unpacking
and public composition remain byte-identical. Its call supplies
`[SE,NW,E,N,SW,NE,S,W]`; selecting argument positions `[2,4,6,8,3,5,7,1]` restores
exactly `[NW,N,NE,W,E,SW,S,SE]`, including the original order. `Life.quorum`
receives the same eight words, center and initial count planes. This control
requires no appeal to approximate equality or a changed behavioral contract.

The held-out family is structurally separate from the development rolling-sum
family. Its base was inspected under the old v3 experiment; it is not claimed to
be a previously unseen Life implementation. The newly constructed helper-support
comparison has no live scores. Reserve it for validation after freezing the
policy and development interpretation. Tuning on that comparison would end its
held-out status and must be disclosed.

## Deterministic checks and remaining evidence

[config-check.json](config-check.json) confirms that all five v3 level arrays and
titles are exact copies, targets are unchanged at family scope, fixture/policy
hashes match, unchanged core text matches within each pair, and the held-out
argument permutation is the stated identity. [parser-check.json](parser-check.json)
records all four fixtures parsing, with 6/8/7/8 declarations and 2,098/2,306/3,141/
3,262 UTF-8 bytes, within the 64-declaration and 49,152-byte limits.

The parent subsequently ran the unchanged pinned Life evaluator on all four
fixtures. [behavior-summary.json](behavior-summary.json) and the individual
[D01](gates/D01/behavior.json), [D02](gates/D02/behavior.json),
[H01](gates/H01/behavior.json) and [H02](gates/H02/behavior.json) receipts pass:
1,537 fixtures plus 21 composition checks on each of Node and Bun, and 28 native
observations per fixture. Their source hashes match the snapshots. The negative
support controls therefore retain the tested Life semantics; this is finite
behavioral evidence, not universal equivalence proof.

Live support calibration is unrun at fixture authoring; no observed model
separation is claimed here. Do not weaken thresholds, reinterpret family failure
as success, or discard negative results to make the new question appear calibrated.
