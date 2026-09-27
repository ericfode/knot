# Local decision-model comparison, 2026-09-26

All four publicly downloadable candidates completed local inference on the
Apple M5 Max / 128 GiB machine. Nimble-9B is the strongest narrow-question
candidate in this small screen. Eikos-27B and AutoJev-27B handle the complete
growing-prefix requirement better. No candidate qualifies as a general default
reviewer from this evidence. Drex 1.1 could not be tried locally because no
public checkpoint/runtime was found.

## Fixed controls and outcomes

The [15 frozen requests](laya-trial/requests.json) are unchanged from the earlier
Laya, Kev-4B and Julia trials: four full-rule requests, eight narrow code requests,
two natural-language sanity requests, and one three-axis style request. Only
`state` and `questions` reach each native runtime. Labels, cohort names and target
paths remain evaluation metadata. The existing source/oracle hashes still
match; the independent deterministic performance oracle was **not rerun**.

The narrow requests ask three questions, but each control is scored only against
its preselected corresponding-family question. The defect threshold remains
0.5. No questions, criteria, labels, temperatures or thresholds were tuned after
seeing these candidates' answers. Native prompt rendering differs between models.

| Model / build | Narrow correct | False positives | Missed defects | Full rule correct |
| --- | ---: | ---: | ---: | ---: |
| Nimble-9B, merged BF16 / MLX | **8/8** | 0 | 0 | 2/4 |
| Eikos-27B, published 4-bit / MLX | 7/8 | 0 | 1 | **4/4** |
| AutoJev-27B, BF16 / PyTorch MPS | 7/8 | 0 | 1 | **4/4** |
| Kev-9B, BF16 / native MLX | 6/8 | 0 | 2 | 2/4 |
| Kev-4B, prior frozen trial | 6/8 | 0 | 2 | 2/4 |
| Julia-1, prior frozen trial | 4/8 | 1 | 3 | 3/4 |
| Laya, prior frozen trial | 4/8 | 4 | 0 | 2/4 |
| Drex 1.1 | Not run | — | — | — |

The four full-rule cases reuse the growing-prefix control sources with a longer
requirement and opposite Boolean meaning: true means the requirement holds.
They are a separate prompt formulation, **not four additional independent code
samples**. The eight narrow controls are correlated pairs. The historical
“held-out” pair was already exposed during Laya development and is not a fresh
qualification set for selecting a winner from this comparison.

| Corresponding defect probability, clean / broken | Eikos | Nimble | AutoJev | Kev-9B |
| --- | --- | --- | --- | --- |
| Original growing prefix | .0759 / .8597 | .1032 / .8481 | .0894 / .5564 | .1451 / .2486 |
| Historical held-out prefix | .1128 / .4533 | .0729 / .5451 | .0726 / .4436 | .0865 / .1878 |
| Invariant summary | .1009 / .9196 | .0428 / .8917 | .0849 / .8134 | .1454 / .7927 |
| Indexed linked list | .0503 / .8872 | .0324 / .9639 | .0381 / .8727 | .1030 / .9170 |

Nimble's difficult prefix detection is only .5451. Its 8/8 result therefore does
not establish high-confidence reliability. On the full rule it accepts both
broken cases, including the original at .8935 probability that the rule holds.
Eikos and AutoJev miss the historical prefix case when asked the narrow question,
but correctly reject it under the full rule. Kev-9B misses both prefix defects
under both formulations; moving from Kev-4B to Kev-9B does not improve these
control outcomes. All four candidates make the expected cancellation and topic
choices on the two language sanity requests.

## Style and timing

All four models consume the complete frozen style descriptions and return full
five-level distributions. This resolves the option-length rejection observed in
Laya and Julia. It does **not** measure whether these models are good taste judges.

The entries below are mean level / probability of level at least 3. Each frozen
axis requires probability at least .6; none reaches that bar. These are the
earlier five-level rubrics, not the subsequently expanded style campaign policy.

| Model | Maximally big brain | Delightful to read | Highly memetic |
| --- | --- | --- | --- |
| Eikos | 2.195 / .345 | 2.136 / .303 | 1.735 / .232 |
| Nimble | 2.394 / .356 | 2.339 / .339 | 2.281 / .341 |
| AutoJev | 2.548 / .561 | 2.152 / .340 | 1.406 / .118 |
| Kev-9B | 2.336 / .387 | 2.753 / .588 | 2.177 / .451 |

Eikos and Nimble do not supply Jev's confidence statistic; the common adapter
preserves their distributions and computes only the expected level. It does not
invent a confidence value or claim drop-in Perch compatibility. Kev's typed
results retain the upstream four-decimal presentation; no narrow decision is
close enough to .5 for that rounding to affect the recorded verdict.

Observed elapsed times per three-question narrow request:

| Model | Minimum / median / maximum, ms |
| --- | --- |
| Eikos | 675.6 / 739.2 / 923.3 |
| Nimble | 261.2 / 274.9 / 822.3 |
| AutoJev | 6072.0 / 6342.7 / 8096.1 |
| Kev-9B | 152.7 / 159.5 / 205.8 |

These are single process runs with different native batching and cache behavior,
without shape-specific warm-up or a controlled background workload. Downloads,
hashing and Nimble's CPU merge overlapped portions of the work. They are execution
receipts, not steady-state latency benchmarks or model-wide speed comparisons.
Eikos and Nimble share a prefix within each request; AutoJev processes one
question at a time to bound memory; Kev uses its native shared-state path.
No state cache is reused between requests.

## Runtime and verification

[Pins](../tools/local-models/pins.json), [setup and commands](../tools/local-models/README.md),
[raw receipts](local-model-trial/), [comparison](local-model-trial/comparison.json)
and [provenance](local-model-trial/provenance.json) make the trial reproducible.
Model weights, installations and clones remain ignored under `.local/`.

- **Eikos:** the author's public `Eikos-27B-MLX-4bit` build and native
  `MLXDecider`; all published file checksums matched. The tested build is
  quantized, and no local BF16 equivalence trial was run.
- **Nimble:** the September 24 checkpoint, pinned Qwen3.5-9B base, verified
  adapter hash and prompt contract; merged on CPU with the published BF16
  preparation recipe and scored with native `ParallelScorer`. T=1 is this
  release's unfitted default. The older v1/v2 calibration is not reused.
- **AutoJev:** native `DecisionModel` and probabilities on MPS. The
  [one-line patch](../tools/local-models/autojev-mps.patch) selects BF16 on MPS
  instead of the upstream non-CUDA FP32 default. No model math, weights,
  temperature or prompt was changed. Transformers used its PyTorch reference
  convolution and recurrent kernels; CUDA acceleration packages were omitted.
  CUDA-versus-MPS numerical parity was not tested.
- **Kev-9B:** the existing pinned Kev runtime with an explicit model selector;
  checkpoint base identity checked before inference. The default selector remains
  Kev-4B. The first offline load rejected a missing `merges.txt`; completing the
  pinned download fixed it before any model predictions were recorded.
- **Drex 1.1:** [access receipt](local-model-trial/drex.json). The
  [vendor page](https://www.nace.ai/drex) offers a hosted API and arranged local
  deployments. No public weights were found; no hosted inference, signup or
  vendor contact was performed. This is unavailable evidence, not a failed
  accuracy score.

**35 focused input-integrity tests passed:** seven each for Eikos, Nimble,
AutoJev, Kev-9B, and the retained Kev-4B path. They cover complete native
encodings, original state/instructions/criteria, ordered Score options, Boolean
polarity, missing or invalid probability mass, empty input and overflow rejection.
The comparison utility reproduces the prior Kev-4B control outcomes and rejects
incomplete or changed-input receipts. No Bend source, accepted law, style rubric,
Perch endpoint or quality threshold was changed; unchanged paid lint checks were
not repeated.

The next qualification candidate is Nimble for atomic questions, with Eikos as
the alternative for full-rule review. Fresh independent controls, including
additional clean cases and prompt-polarity checks, are still needed before
changing the default reviewer. This trial installs no service and makes no
automatic source edits.
