# Whole-program Galaxy brain, supporting helpers

Re-evaluating all 63 saved Life submissions changes the helper assessment but
produces **zero full passes**. Of 61 parseable submissions, 49 have every
declaration meet the new support target. None meets the whole-program Galaxy
target. The highest probability mass at Galaxy level is 10%; the threshold is
60%. These are model judgments, not measured human preferences.

The source files and their original receipts are unchanged. Two syntax-rejected
submissions remain explicit nonpasses. Two additional parseable submissions that
failed compiler/behavior gates receive style judgments but cannot pass overall.
The manifest preserves all four failures and the earlier semantic failure.

| Saved group | Submissions | New complete reviews | All declarations support the idea | Old full passes | New full passes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original two authors, v2 | 2 | 2 | 2 | 0 | 0 |
| Original continuation rounds, v2 | 16 | 15 | 12 | 1 | 0 |
| Interrupted R2 search, v3 | 45 | 44 | 35 | 0 | 0 |
| Total | 63 | 61 | 49 | 1 | 0 |

The earlier v2 success used conceptual-compression level 3 and three axes.
It is still a recorded v2 success; it was never evidence of Galaxy level 5.
Do not treat its different outcome here as a code regression. R2's previous
all-declaration Galaxy policy and this whole-program policy both produce zero
full passes on the same 45 submissions.

## What changed

The user's criterion is: **helpers should support the main thing being Galaxy
brain**. [The frozen experimental policy](config.json) asks two separate questions:

1. Does the complete collaborating program earn Galaxy brain, and meet the
   four existing Delight, Memetic, Anticipation and Payoff targets?
2. Does every parsed declaration perform a useful role with proportionate cost,
   consistent conventions and a legible contribution to the main mechanism?

The five existing level descriptions are unchanged. Galaxy requires level 5;
the other family axes require at least level 3. Every declaration requires at
least support level 3. Each target needs probability mass of at least 0.60.
Helpers need no independent novelty. Datatypes, laws, adapters and core functions
are included; names and author-declared roles provide no exemption. Strong
helpers cannot supply a missing whole-program Galaxy judgment.

There is no combined style score. Old per-declaration ratings and new family /
support ratings ask different questions, so averaging or subtracting their
fractions would be misleading. The full-pass outcome remains comparable as an
explicit decision under each named policy, with its differing requirements.

## What the scores reveal

The packed-row implementation, R2 T006 round 3, is the strongest family on
Galaxy mass: 10% Galaxy and 70% at level 4. It passes the other four family
targets and all seven support judgments. Its conventional `Life.pack` helper
previously received 1% at Galaxy level; it now receives 93% at the support
target. That is a changed question, not a 92-point improvement in the code.

The polynomial implementation, T004 round 3, passes all support judgments and
the four other family axes, but has only 1% Galaxy mass. The original induced
v2 winner, arm B round 6, passes all four support judgments but has 0% Galaxy
mass and uncertain Anticipation (55%).

Across the 61 reviewed families, Delight and Payoff pass in all 61; Memetic
passes in 57; Anticipation passes in 34; Galaxy passes in none. Of 424 individual
support assessments, 407 meet the support target. The remaining obstacle is
therefore not simply asking too much of ordinary helpers. This collection has
well-fitted, often appealing implementations without evidence that the main
mechanism satisfies the stated Galaxy bar.

## Calibration limits

Expectations were [recorded before live calls](calibration/expectations.json),
then policy and reviewer hashes were [frozen](policy-freeze.json). All four
controls passed the unchanged finite behavior gate. New negative controls also
received clean semantic review; unchanged positive sources reuse their existing
semantic receipts. No universal equivalence proof is claimed.

| Comparison | Clean helper support | Altered helper support | Added indirection | Result |
| --- | ---: | ---: | ---: | --- |
| Development: zero-default head | 95% | 48%, uncertain | 4–5%, below target | Expected separation |
| Held out: neighbor layout | 94% | 81%, meets target | Route 78%, meets target | Absolute-target separation failed |

The development pair distinguishes straightforward support from obvious
useless relays. The held-out pair exposes permissiveness toward an unnecessary
argument permutation. The clean version ranks higher, but both altered
declarations still pass. [The interpretation](calibration/held-out-interpretation.json)
was recorded without tuning or rerolling. **This policy remains provisional and
is not qualified for adoption as the global automatic style gate.** The requested
rescoring and Parallax trial use it as an explicitly named experimental standard.

## Evidence and reproduction

[results.json](results.json) retains per-source judgments and separate v2/v3
comparisons. [manifest.json](manifest.json) identifies all 63 original source
hashes and retained fixed gates. [The complete review](receipts/runs/ec8dcc5eeb1ad6efe74cb25f25f91be9f4849f243dfebe8c4693379d593430d6.json)
links raw requests, responses, distributions, usage and actual Jev 1.13.0 model
identity. It completed 485 unique requests, reusing 15 exact calibration
responses and making 470 fresh calls, with at most two in flight.

The reviewer supplies the entire source under `composition.bend`, with parsed
declaration spans and the contract. It sends no trial ID, author model, condition,
old score, receipt path or calibration expectation. Oversize input, syntax
failure, empty coverage, changed hashes and incomplete responses cannot pass.
Completed identities are reused exactly; failed identities never retry
automatically. The full saved batch took 26.334 seconds, including receipt reuse;
this is judge wall time, not author latency or program performance.

```sh
python3 research/life-helper-review/prepare.py
python3 research/life-helper-review/analyze.py
node --test research/life-helper-review/review.test.mjs
```

The [rebase receipt](rebase.json) records main `449bb57` and preserved historical
artifacts. The original R2 lock is retained at branch
`codex/life-inducer-r2-frozen`; rebasing changed documentation and `package.json`,
not the original source/receipts or style engine. This re-evaluation adds new
receipts and does not rewrite the old campaign.

[Independent receipt audit](audit-results-all.json) verifies all source hashes,
parsed inventories, raw requests/responses, actual model identities, coverage and
pass calculations with zero discrepancies. Development and held-out receipt
audits also pass; this does not reverse the held-out rubric failure. The reviewer
has 20 passing offline tests and the auditor has 13 passing mutation tests. The
[bounded law packet](LAW_REVIEW.md) received eight relevant checks with no
threshold finding; its actual model was Jev 1.13.0.

```sh
python3 research/life-helper-review/audit.py \
  --manifest research/life-helper-review/manifest.json \
  --config research/life-helper-review/config.json \
  --report research/life-helper-review/receipts/runs/ec8dcc5eeb1ad6efe74cb25f25f91be9f4849f243dfebe8c4693379d593430d6.json \
  --output /tmp/life-helper-review-audit.json
```
