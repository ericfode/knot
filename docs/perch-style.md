# Style quality checks

The target is a distinctive code aesthetic: **Maximally big brain**,
**Delightful to read — high dopamine**, and **Highly memetic**. Every existing
parsed declaration is assessed against all three; an alternative implementation
is not required. Rankings are a secondary view of those independent ratings.

Version 3 adopts the [research-informed refinements](perch-memetic-criteria-proposal.md)
to memetic identity and separates **Anticipation** and **Payoff** into their own
0–4 scales. They are required for every declaration with at least marginal
contract importance, including uncertain classifications and critical datatypes.
The [research on ideas generally](memetic-ideas-research-2026-09-26.md) motivates
these taste criteria; it does not validate the model's judgments. Existing
receipts retain their original rubric identity and meaning.

| Axis | Desired experience |
| --- | --- |
| Maximally big brain | A small expressive algebra or representation absorbs cases and exposes invariants. Each abstraction explains more than it adds. |
| Delightful to read — high dopamine | Exact names, rhythmic layout, symmetry and dense composition create repeated satisfying moments where the structure clicks. |
| Highly memetic | The code has its own ideas, vocabulary and felt rhythm: an earned hook gets into your head, rewards insider fluency, and makes you want to read, write and share more of this particular style. |

Memetic is used in the internet sense. Mere recall or ease of teaching is not the
whole goal. The form should land: motifs repeat with variation, an expression
has a satisfying turn, and mechanism, words and visual shape establish a
recognizable identity. Knowing the vocabulary unlocks the ideas and creates a
shared grammar. A distinctive aesthetic can teach the reader what to anticipate
and then reward that anticipation. This describes the desired reading experience,
not a measured psychological effect. Decorative slogans and self-praise do not
substitute for the code's actual character.

Terse notation, learned idioms and dense composition are welcome. Simple helpers
can qualify through one fitting operation or resonant expression; adding layers
solely to look clever would work against the goal. Correctness, quantity, proofs,
backend behavior and performance remain independent deterministic gates.

## Run it

```sh
# Rate each existing declaration in a file. No competitor needed.
npm run lint:style -- --live src/scope.bend

# Rate one parsed declaration, including datatypes.
npm run lint:style -- --live src/scope.bend::alternatives
npm run lint:style -- --live src/scope.bend::Scope

# Rate the project and retain the complete report.
npm run lint:style -- --live --all --output=.local/style-project.json
```

`lint:rank` remains an alias. `--cohort='optional purpose or contract'` adds context
when useful; omitting it rates each declaration relative to its own purpose.
`--json` prints the structured report. An output path ending in `.gz` saves the
same JSON losslessly compressed; `--reuse` accepts either form. `--jobs=N` sets concurrency from 1 to 16;
project mode defaults to 8, explicit targets to 1. The maximum inventory size is
5,000 declarations by default; exceeding it fails preflight rather than silently
truncating coverage. No automatic request retries are made.

`--all` discovers tracked and nonignored new `.bend` files using Git. It includes
compiler code, packages, research, laws, proofs, fixtures and retained experiments.
Ignored dependencies, caches and build directories are not project source. Exact
parser spans identify definitions, law declarations/fills and datatypes. Files
that cannot be parsed or supplied with valid context are listed in
`inventory.unranked`; files without any supported declaration are listed separately.
An incomplete run cannot claim that everything was rated.

Function/law context uses the same pinned Bend parser and bounded working-copy
helpers as normal Perch checks. Datatype context includes sibling datatypes and
up to four direct same-file users found through parsed references; imported and
transitive datatype dependencies are explicitly unresolved. Every target retains
source and context hashes, truncation markers and unresolved references. Syntax
parsing does not establish typing or dependency completeness.

Input/context hashes are checked before requests and again afterward. Changes
during review are reported; the ratings still refer to the recorded snapshot.
An existing output file is rejected before paid requests. Every dispatched run
also writes a secret-free local receipt under `.perch/usage/`.

`--reuse=path/to/earlier.json` reuses only rows with matching target source,
request-state, context, parser, rubric and requested-model identities. Reused and
fresh rows must resolve to one model. Completed answers from a failed run are
retained for explicit reuse; a provider failure itself yields no partial rankings
or assessments. This allows recovery without paying again for unchanged answers.

## Interpret the result

[perch-style.json](../perch-style.json) contains three primary rubrics and two
separate reading-experience scales. Big brain runs from 0 to 5; the other four
run from 0 to 4. Functions, laws, proofs and datatypes receive these five typed
Score questions plus a binary `criticality` Score in the same request. Known
truncation withholds the two reading-experience questions, leaving four questions
and explicit unavailable ratings. Criticality selects requirements; it is not
another taste axis. Each declaration receives its own distributions, independent
of other candidates or their order.

The memetic ladder is **Unformed → Ordinary → Recognizable → Contagious →
Generative grammar**. Level 3 requires an earned hook carrying a substantive
relationship worth quoting or adapting. One sharp expression can suffice.
Level 4 requires a traceable grammar for further expressions. Popularity,
actual sharing and an existing community require separate social evidence.

| Level | Anticipation | Payoff |
| --- | --- | --- |
| 0 | Disoriented | Unresolved |
| 1 | Passive | Flat |
| 2 | Guided | Fitting |
| 3 | Inviting | Earned |
| 4 | Compelling | Resonant |

Anticipation asks how the expression prepares the reader for an inviting next
relationship. Payoff asks how satisfyingly the expression fulfills, varies or
reframes that expectation. Confirmation and surprise can both qualify. Tiny
helpers can provide an immediate setup and resolution; extra buildup earns no
credit. Keep both distributions separate from overall Delight: neither their
average nor one exceptional score can substitute for the other requirement.

Big brain level 4 rewards an unusually economical solution. Level 5, **Galaxy
brain**, rewards a surprising reframing: apparently essential distinctions become
consequences of one principle, revealing further connections that can be traced
through the supplied mechanism. Complexity or obscurity alone does not qualify.
The new level is a user-requested taste criterion; human calibration remains
pending. Earlier receipts retain their original rubric identity and cannot be
reused as ratings under the expanded scale.

The default target is **level 3 or higher** on all three primary axes. A
critical or uncertain function, law or proof must instead reach **Galaxy brain,
level 5**, on big brain. Critical or uncertain declarations of **every kind**
must also reach **Anticipation 3 (Inviting)** and **Payoff 3 (Earned)**. Datatypes
retain the ordinary big-brain target. Anticipation and Payoff remain visible
but advisory for declarations confidently classified as noncritical.

Criticality includes a defining or supporting material role in a contract, core
algorithm, invariant, trust boundary, valid state representation or proof
obligation. Even marginal contract importance qualifies. Noncritical requires
an incidental, cosmetic or illustrative role with no material contract role.
Size and current elegance do not determine importance; poorly written critical
code is still critical.

Criticality of at least 60% is `critical`; at most 40% is `noncritical` only when
context is not truncated. Intermediate or context-limited judgments are
`uncertain`. Both critical and uncertain declarations receive the applicable
stricter requirements above. A missing or malformed classification fails review
rather than granting the default bar. Uncertain criticality can satisfy the style
gate by meeting every stricter requirement when sufficient context is available.

For big brain, sum normalized probability mass on **level 5 alone** when the
stricter requirement applies; otherwise use levels 3–5. Delight and memetic
identity, Anticipation and Payoff use levels 3–4. Each required distribution is
judged separately:

- At least 60%: `meets_target`.
- At most 40%: `below_target`.
- Between those bounds: `uncertain`.

All applicable targets must be met for a declaration to pass automatically:
three for noncritical declarations and five for critical or uncertain ones.
Truncated context makes Anticipation and Payoff `unavailable`, without fabricating
a zero score. An unavailable required rating prevents a pass. Unresolved
references are disclosed as `limited_context`; inspect whether the missing
material is necessary to judge the supplied expression.

Receipts retain `rubric_version`, `criticality.policy`, all returned distributions
in `rows[].answers`, and `criticality.assessments`. Each required style assessment
records its effective `target_level`, `minimum_probability` and `target_basis`.
`diagnostics.assessments` records both reading-experience scales, their context
limits and whether each is required or advisory. `style_summary.by_axis` counts
only applicable requirements. Rankings remain a secondary view of the three
primary axes. Reuse validates every requested answer; policy and wording changes
invalidate old receipts through the rubric hash.

The 60% policy is an explicit provisional review threshold, not a calibrated
probability of agreement with the user. Full distributions remain available;
model confidence is distribution concentration, not correctness or taste agreement.
A model can misclassify importance; review criticality alongside the source and
its contract. Calibration of the new classifier remains separate from proving
that the command enforces its selected threshold.
A high rank alone cannot satisfy the quality bar. Even the first-ranked item can
be below target.

Exit 0 means complete, current coverage and all selected units meeting every bar.
Exit 3 means style attention is needed: a below-target, uncertain or unavailable
required rating, or stale source.
Exit 1 means the run failed or coverage is incomplete. These checks guide review;
they do not replace semantic gates or authorize changing a correct contract.

Inspect low-rated code, identify a concrete improvement, and retain the original
contract and independent tests. Record disagreements and compare actual proposed
changes when available. Do not force obscurity, branding, verbosity or churn to
satisfy the model. Human preferences and held-out examples must guide calibration.

Perch 0.3.5's ordinary custom-check path expects Noul answers. This project's
companion command supplies the Score path through the same provider and existing
project credentials. Normal `npm run lint` still reports defect/performance/law
checks; **it does not include these style ratings**. During development, run both
applicable checks and report their coverage separately.

The complete project pass and a live example are recorded in
[the three-axis report](perch-style-project-2026-09-26.md).
That report predates version 3. The current policy's focused verification and
live context-limit check are recorded in
[the version-3 integration evidence](perch-calibration/style-v3-2026-09-27/README.md).

The user has started an [implementation campaign](STYLE-CAMPAIGN.md) to improve
the whole inventory. Its owner queue, continuation policy and receipt-aware
baseline inventory live in `docs/style-campaign/`. The campaign preserves
independent acceptance and records unresolved taste judgments explicitly.
Its inventory's `matches_all_required_baseline_targets` field includes the
conditional requirements. The legacy `matches_all_three_baseline_targets` field
is retained as a conservative alias: it cannot report a pass when a required
Anticipation or Payoff rating fails. Older rubric identities are incompatible
with the current baseline comparison.

## Historical two-axis comparison pilot

The pilot below used version 1, required competing implementations, and did not
include the memetic axis. Its distributions are historical evidence and must not
be combined with the current rubric as if the instructions were identical.

### Pilot — 2026-09-26

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

That pilot's proposed next step was a comparison of real compiler alternatives.
The user's later instruction supersedes comparison-only coverage: routinely
assess existing declarations against the three quality targets. Human preferences
recorded before review and fresh held-out examples are still needed to calibrate
agreement with the intended taste. Track unwanted obscurity, verbosity and novelty
incentives separately from defect precision; preserve deterministic acceptance.
