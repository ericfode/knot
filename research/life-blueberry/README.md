# Game of Life with and without the Blueberry inducer

Both implementations pass the independent behavior gates. Neither meets the complete unchanged Perch style bar. The exposed candidate passes all three axes on 5 of 7 declarations; the unexposed candidate on 6 of 13. This single pair does not establish an inducer effect.

## Design and frozen conditions

Two delegated GPT-6 Astra agents at max reasoning began in fresh contexts. Both received the same contract, style rubric and permitted Bend references. Arm-a received no inducer; arm-b read the entire 9,532-byte decoded payload selected by the user from the linked chat. Its SHA-256 is `3ac9b312db6b6c11c2fcef869b1fbf69cfaa8a8628dd5ce7ff26e51cf2596ef4`. The original envelope and decoder are preserved.

The contract and independent corpus were committed before dispatch in `c115ba6`. One candidate per arm was allowed, with at most one compiler-diagnostic repair. No author received runtime-oracle or Perch feedback. No source was revised after its successful compiler check. Initial sources and the one repair remain available.

The active rubric was frozen at SHA-256 `89600125d9679973c00754e88957e4b26ba404c75fa06b4fd83ff5595e5036d2`. Each declaration needs at least 60% normalized probability mass on level 3 or higher on every axis. The general-ideas memetic research draft was not installed or used to rescore this experiment.

## Results

| Observation | Without inducer: arm-a | With inducer: arm-b |
| --- | ---: | ---: |
| Initial compiler check | Failed | Passed |
| Compiler-diagnostic repairs | 1 | 0 |
| Final checker and behavior gates | Passed | Passed |
| Conceptual compression target | 13/13 | 7/7 |
| Delight target | 13/13 | 6/7; one uncertain |
| Memetic target | 6/13; six below, one uncertain | 5/7; one below, one uncertain |
| All three targets together | 6/13 | 5/7 |
| Whole implementation style pass | No | No |

Counts refer to declarations, not repeated trials or independent participants. Both public `step` definitions receive 0.88 probability mass at the memetic target. Their `evolve` definitions receive 0.83 and 0.82. The main difference in pass fractions is in helper declarations. Different decompositions give different denominators; this is not a controlled effect-size estimate.

## Deterministic evidence

Each candidate passes 1,537 complete-board observations and 21 composition checks under both Node and Bun, plus 28 selected native CPU observations. Small-board tests exhaust all binary inputs for the dimensions listed in [the law packet](LAW_REVIEW.md), including all 512 3x3 boards. Canonical cases cover a block, blinker, translated glider and corner birth; seeded larger rectangles reach 32x32. Native cases are a smaller selected set, up to width 8.

Three type-correct bad controls are rejected by actual state mismatches: unchanged input (1,455 corpus failures), all-dead output (1,025), and always advancing one step (553 plus 20 composition failures). They expose behavioral and composition errors without changing the frozen assertions. No universal proof, GPU execution or performance advantage is claimed.

## Perch evidence

The style judge was `jev-1.13.0`: 20 requests, 20 responses, no reused ratings, no stale sources and no context truncation. Neutral review paths contain no condition labels; reconstructed request states match the recorded hashes. Base primitives remain marked unresolved-or-builtin in the model context; the deterministic compiler resolves them separately.

Targeted semantic review completed 80 relevant source checks over all 20 definitions, with no findings at the configured thresholds. The bounded law packet completed eight checks with no threshold findings. All 21 semantic/law requests received responses from the same model. These are advisory observations; the raw below-threshold probabilities are retained.

### Per-declaration target probability

Numbers are normalized probability mass on level 3 or higher. They are model judgments, not calibrated probabilities of human agreement. Full ordinal distributions and concentration measures are in [the raw style receipt](receipts/style.json).

#### Without inducer

| Declaration | Compression | Delight | Memetic |
| --- | ---: | ---: | ---: |
| `row.pack` | 0.94 | 0.77 | 0.07 |
| `row.unpack` | 0.95 | 0.81 | 0.02 |
| `rows.pack` | 0.78 | 0.80 | 0.11 |
| `rows.unpack` | 0.77 | 0.72 | 0.06 |
| `tally` | 0.97 | 0.90 | 0.32 |
| `halo` | 0.88 | 0.72 | 0.21 |
| `census.rule` | 0.68 | 0.75 | 0.49 |
| `census.spread` | 0.83 | 0.87 | 0.70 |
| `row.step` | 0.75 | 0.85 | 0.73 |
| `rows.sweep` | 0.83 | 0.85 | 0.76 |
| `rows.step` | 0.85 | 0.90 | 0.84 |
| `step` | 0.86 | 0.93 | 0.88 |
| `evolve` | 0.74 | 0.75 | 0.83 |

#### With inducer

| Declaration | Compression | Delight | Memetic |
| --- | ---: | ---: | ---: |
| `front` | 0.88 | 0.75 | 0.74 |
| `halo` | 0.86 | 0.74 | 0.51 |
| `pulse` | 0.91 | 0.88 | 0.62 |
| `strips` | 0.89 | 0.59 | 0.01 |
| `sweep` | 0.82 | 0.89 | 0.85 |
| `step` | 0.87 | 0.95 | 0.88 |
| `evolve` | 0.75 | 0.81 | 0.82 |

## What the two authors wrote

**Without exposure:** [packed-row implementation](arms/arm-a/life.bend). A lane-wise full adder is reused across both axes. The population census includes the center, reducing the final selection to total three, or total four with a live center. Separate packing/unpacking operations connect that representation to the fixed list interface.

**With exposure:** [row-stencil implementation](arms/arm-b/life.bend). A horizontal halo sums three cells. A pulse combines three halos and subtracts the center to form the eight-neighbor ring. A sweep carries the old center halo forward.

Both independently chose halo vocabulary and a moving row window. Their presence alone cannot be attributed to exposure. The exposed author reports inspiration from the glyph field's repeated frames and missing centers; that is an author report, not causal identification.

## Review disposition and next useful questions

The sources are retained as experiment results. They are not rewritten to cross the observed thresholds. The former campaign pilot and broader queue remain on hold; this completes only the explicitly requested two-arm experiment.

- In arm-a, four pack/unpack adapters are far below the memetic bar. A future design could investigate the representation boundary as a coherent reader-facing operation, with fixed correctness and performance evidence. That would be a new candidate, not a repair of this experiment.
- Arm-a's `census.rule` is uncertain on memetic identity (0.49), while `tally` is below (0.32). The carry-plane relationship is the main explanation burden. `halo` is also below (0.21): its one-call wrapper makes less of the family's mechanism visible locally. Their compression and delight ratings remain separate observations.
- In arm-b, `halo` is uncertain on memetic identity (0.51). `strips` is below (0.01) and uncertain on delight (0.59). Its dimension-to-row adapter is a concrete reading seam to inspect, rather than a reason to decorate the source.
- A calibration question remains: should every adapter carry an independent hook, or should some identity judgments concern the interacting family? Here the unchanged per-declaration rule decides the result. Fresh examples and human preferences would be needed before changing it.

One author draw per condition, unequal helper inventories, stochastic generation and no matched-length placebo limit inference. There is no statistical significance claim, no human taste calibration, and no evidence that invisible encoding itself caused a result: the exposed author read decoded text. Reading compliance is supported by fresh contexts and author records, not a filesystem sandbox.

## Reproduction and retained artifacts

- [Contract](CONTRACT.md), [identical author packet](AUTHOR.md), [preregistration](preregistration.json) and [dispatch/setup](dispatch-and-setup.json).
- [Submission hashes and neutral mapping](submission-lock.json), [machine-readable results](results.json), and [law packet](LAW_REVIEW.md).
- Author notes, initial/repaired snapshots, compiler streams and receipts in each arm directory.
- [Frozen fixture/oracle generator](gates/fixtures.mjs), [runtime runner](gates/run.mjs), [evaluator](gates/evaluate.py), and [Perch invocation recorder](review-live.py).
- [Reconstructed judge inputs](receipts/judge-inputs.json.gz); ordinal and Noul receipts in receipts/.

To repeat deterministic evaluation, use a new receipt filename so the previous run is preserved:

    python3 research/life-blueberry/gates/evaluate.py research/life-blueberry/arms/arm-a/life.bend research/life-blueberry/receipts/arm-a-gates-repeat.json

The neutral files under .local/life-review are ignored working copies. Restore them from submission-lock.json's source paths with the same hashes before reproducing judge input construction. Do not rerun unchanged paid reviews merely to obtain a more favorable score.
