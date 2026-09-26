# Ranked style review

The target is **high dopamine to read**: dense code with conceptual payoff,
satisfying symmetry, an expressive little vocabulary, and repeated moments
where the structure clicks. Terse notation and learned idioms can serve that
taste. Readability here means rewarding a fluent reader, not maximizing prose
or minimizing unfamiliarity.

Two independent ordinal rubrics live in [perch-style.json](../perch-style.json):

| Ranking | What earns a high position |
| --- | --- |
| Maximally big brain | A small algebra or representation absorbs cases; definitions compose; each abstraction explains more than it adds. |
| Delightful to read — high dopamine | Exact names, rhythmic layout, balanced forms and dense composition produce satisfying recognition and a memorable sense of fit. |

Each rubric has five descriptive levels. The command asks a typed Score question
for each axis, then sorts by its expected level. The terminal displays ranks;
JSON retains the underlying scores, confidence and complete distributions.
No combined score or style failure is produced. Correctness and performance
remain separate gates. Comments praising the code are explicitly ignored.

## Use

```sh
npm run lint:rank -- --live \
  --cohort='Map each U32 x to 3*x+1 modulo 2^32 over a reusable list, preserving length and order.' \
  tests/perch-style/a.bend::solve \
  tests/perch-style/b.bend::solve \
  tests/perch-style/c.bend::solve
```

Compare alternatives to a shared task or genuinely comparable units; describe
that task with `--cohort`. A whole file selects its parsed declarations; `::name`
selects one. At least two distinct units are required, with a default maximum
of 12. Prefer explicit named targets. The command uses the existing project key
and endpoint. Both questions share one provider request per unit.

Add `--json` for structured output and `--output=path.json` to retain evidence.
An existing output path is rejected before model calls. Every dispatched run
also leaves an ignored `.perch/usage/` receipt. Provider failures retain failed
coverage and produce no partial ranking. Syntax, empty selections and excessive
scope are rejected before calls. Requests are not automatically retried.

The implementation in [scripts/perch-style.mjs](../scripts/perch-style.mjs) uses
the same pinned Bend parser and working-copy helper/law/datatype context as
normal Perch checks. Hashes identify the source, bounded context and rubric.
Context limits and unresolved references remain visible. Parsing does not
establish typing, proof acceptance, behavioral equivalence or backend support.

Perch 0.3.5 recognizes Score configuration, but its custom-check execution path
still expects a `noul` answer. This project command supplies the ordinal path
directly through the same provider; native `perch check` and `perch rules list`
do not run or list these rubrics. Existing defect rules remain unchanged.
The provider's [Score documentation](https://docs.typesafe.ai/primitives/score)
defines the ordered criteria and response distribution, and the
[API reference](https://docs.typesafe.ai/api) defines the request format.

## Interpret ranks

A rank is an ordering within this cohort, not a probability that the code is
good. Equal scores share a rank. Adjacent gaps below 0.25 on the 0–4 rubric
are marked `near tie above`; this threshold is a display convention, not a
significance test. The first item in a near-tied group is not a decisive winner.
Confidence describes concentration of the level distribution, not agreement
with the user's taste. Inspect the distribution when making a style decision.

Each candidate is evaluated independently; the model does not see the other
candidates or their order. Sorting happens locally. This supports reuse of
descriptive rubrics but does not establish pairwise preference accuracy.
Do not compare unrelated algorithms, different rubric hashes or different
resolved models as though their positions were interchangeable.

## Pilot — 2026-09-26

Three [specimens](../tests/perch-style/README.md) implement the same list mapping.
The frozen performance evaluator independently accepted all three: Bend 2.0.29
compilation, 19 output probes per candidate, and operation-count scaling through
1,024 elements. These finite gates do not prove arbitrary-input equivalence or
safe stack depth on every backend. Five targeted `perf-growing-prefix-copy`
checks covered every declaration, with zero findings.

Two live runs used `jev-1.13.0`, with the second reversing request order.
Both returned the same rank order, with small changes in scores and distributions:

| Implementation | Maximally big brain | High dopamine to read |
| --- | ---: | ---: |
| Direct recursion (`a`) | 3 | 3 |
| Mapping combinator (`b`) | 2 | 1 |
| Accumulator and reversal (`c`) | 1 | 2 |

**Every adjacent pair was a near tie on both axes.** In the first run, big-brain
means spanned only 2.31–2.39; delight means spanned 2.43–2.71. This confirms a working ranking
path with two distinct orderings, not strong aesthetic separation. Repeating
identical requests may benefit from provider determinism or caching; these two
runs are not independent evidence of judgment quality. The rubric was not tuned
to make a particular specimen win.

The two runs made six requests with 12 Score answers, consuming 7,376 input
tokens and 234 output tokens. They took 521 ms and 316 ms respectively. Timings
measure these runs only and do not establish sustained provider latency.

Evidence: [first ranking](perch-calibration/style-2026-09-26.json),
[reverse-order repeat](perch-calibration/style-reversed-2026-09-26.json),
[deterministic gates and source-rule receipts](perch-calibration/style-gates-2026-09-26.json).
Twenty-one offline tests and the law-rule wiring gate passed, including malformed
answers, missing credentials, partial failure, model drift, exact declaration
selection and secret-free receipt checks.

The next calibration input should be real compiler alternatives with a human
preference recorded before model review. Check fresh held-out examples after
any rubric change. Track preference agreement and unwanted verbosity or
cleverness incentives separately from defect precision. Keep the style command
opt-in and advisory until that evidence exists.
