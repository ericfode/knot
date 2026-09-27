# Do the style rules recognize established memetic prose?

**Yes on the memetic axis: 4/4 positive examples meet its target. No on the
five-axis conjunction: 0/4 meet all five targets.** The memetic question also
accepts a wordplay control that the user subsequently judged vacuous and memetic.
The assistant's original negative label was wrong for the user's intended axis.

The user requested examples of “objectively memetastic” things on 2026-09-27,
following a proposal to apply Perch to system documentation. We operationalized
that as technical expressions with documented reuse. Cultural uptake is
observable; aesthetic quality is not an objective label. These are
assistant-selected positive hypotheses, not user-rated examples.

## Sources and prior expectations

- **[Zen of Python](https://peps.python.org/pep-0020/):** active informational PEP,
  public-domain text, and the documented `import this` Easter egg. The specimen
  is the complete 19-aphorism block. Repeated comparisons establish a grammar;
  qualifications vary it. Expected to meet the memetic target.
- **[Go shared-memory proverb](https://go.dev/doc/effective_go#sharing):**
  quoted and attributed in the [Rust book](https://doc.rust-lang.org/book/ch16-02-message-passing.html).
  That is concrete reuse across language communities. The specimen is the
  11-word slogan. Its exchange of means and end carries a concurrency idea.
  Expected to meet the memetic target.
- **[Unix philosophy](https://cscie2x.dce.harvard.edu/hw/ch01s06.html):**
  Raymond's chapter, mirrored in a Harvard course, relays McIlroy's formulation
  through Salus and develops its compositional implications. The original
  McIlroy/Salus volume was not inspected. The specimen includes only the first
  two prescriptions, 15 words. Parallel imperatives connect specialization to
  composition. Expected to meet the memetic target.
- **[Postel's robustness principle](https://www.rfc-editor.org/rfc/rfc793.html#section-2.10):**
  recorded in RFC 793 (1981), with its influence and limitations revisited in
  [RFC 9413](https://www.rfc-editor.org/rfc/rfc9413.html#section-2) (2023).
  The specimen is the 14-word principle. Balanced opposition expresses
  asymmetric obligations. Expected to meet the memetic target; this does not
  endorse every application of its technical advice.

Each original has an assistant-written plain rewrite. Before scoring, the
expectation was that the original would exceed its rewrite by at least 15
percentage points in memetic target mass. These are imperfect form ablations:
length, nuance and familiarity also differ.

Two further specimens were fixed before scoring: invented chiasmus intended to
lack an explained technical relationship (expected below target), and the first
paragraph of Knot's [selected execution direction](../../EXECUTION-MODEL-CASE.md)
(open hypothesis). That paragraph does not stand for the whole document.

## Method and scope

[cases.json](cases.json) records exact texts, provenance, hypotheses, order and
limitations. [freeze.json](freeze.json) records their identities before any
requests, at base commit `3dc7774b69d6eedc8a4e32bbbe91a57cf89f396b`.
The production v5 [rubric snapshot](rubric.json) has SHA-256
`c7de14e38c3b57eec32ad822cfeb08bd1abc5c87ed2e5bdd649c44c1eed316ec`.

The production `lint:style` command accepts parsed Bend. This probe instead calls
its existing `evaluateStyle` with all five **unchanged** style questions and
prose states. No attribution, URL, cultural evidence, expected label, prior score
or paired rewrite is included in an individual request. All passages are treated
as leading expressions, so no helper exemption applies. Famous wording remains
recognizable; this is not blind to model familiarity or training exposure.

Jev **1.13.0** returned all 10 serial requests, each with five complete Score
distributions. There were no retries or rubric edits. Exact request payloads are
in `requests/`; successful response bodies and hashes are in `responses/`.
[results.json](results.json) retains all distributions, provider confidence,
usage, model identity, elapsed time and assessments.

Each axis uses the existing leading threshold: at least **60% probability mass
at level 3 or above**. Mass at most 40% is below target; the intervening range is
uncertain. Percentages below are model distributions under this prompt, not
probabilities that humans will share a passage. The five-axis conjunction is a
diagnostic prose result. It omits parsing, role classification, task potential
and executable composition checks, and is **not a full Bend style pass**.

## Results

Bold numbers meet their axis target. All rows fail the five-axis conjunction.

| Specimen | Compression | Delight | Memetic | Anticipation | Payoff |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zen of Python | 9% | **65%** | **98%** | 55% | 33% |
| Go proverb | **76%** | 41% | **93%** | 54% | 29% |
| Unix two-prescription excerpt | **78%** | 41% | **93%** | 56% | 21% |
| Postel's principle | **82%** | 35% | **96%** | 31% | 23% |
| Zen plain rewrite | 16% | 17% | 58% | 22% | 15% |
| Go plain rewrite | **82%** | 12% | **61%** | 26% | 11% |
| Unix plain rewrite | **61%** | 6% | 14% | 24% | 6% |
| Postel plain rewrite | **76%** | 8% | 45% | 36% | 18% |
| Empty wordplay | 30% | **60%** | **78%** | 49% | 19% |
| Knot selected-direction paragraph | 43% | 54% | **60%** | **74%** | 8% |

The original-minus-rewrite memetic gaps are **40 points** for Zen, **32** for Go,
**79** for Unix, and **51** for Postel. All four exceed the predeclared 15-point
gap. The Go rewrite still passes outright: losing a rhetorical device need not
eliminate the idea's expressive pull. The pair expectation was relative, not
that every rewrite must fail.

The invented negative control is:

> The task is the map; the map is the task. Frame the flame; flame the frame.
> Queues remember futures; futures remember queues.

Its **78% memetic** result contradicts the recorded negative expectation. The
initial report called this a false positive because the memetic question requires
a substantive relationship and rejects mere word repetition. The user then
asked why it was a false positive. That exposed an unsupported step: the
assistant's intended negative label was not independently established.

The passage does not specify how tasks, frames and queues cooperate, but
“queues remember futures” can invite a meaningful interpretation. The positive
aphorisms also rely on reader inference. Requiring a complete mechanism from
this control while accepting an implicit relationship in the positives would
skew the comparison. Catchiness can also exist without technical truth.
The user then clarified: “something can be memetid without being valuable” and
“it's vacous, but it is memetic”. **Disposition: human-adjudicated memetic and
vacuous; the assistant's negative label is rejected.** No numerical level was
assigned by the user. The original expected label and response remain unchanged
in the frozen experiment. The result is not a false positive under that clarified
objective. The code-oriented input domain is a separate limitation.

## What this changes

The memetic question recognizes all four selected examples and prefers their
forms to plain rewrites. That is useful small-sample evidence, not an accuracy
estimate. The wordplay result also agrees with the user's later judgment. This
set now has no independently accepted nonmemetic control, so it cannot establish
specificity. Low conceptual value does not supply a negative memetic label.

None of the positive examples reaches the Payoff target, and only Zen reaches
the Delight target. Anticipation is uncertain for three and below target for
Postel. The rubric describes parsed declarations and collaborating mechanisms;
applying its entire conjunction to aphorisms is an unvalidated transfer. Scope
mismatch is a plausible explanation, not a proven cause: the retained responses
contain distributions, not explanations.

The Knot paragraph passes memetic exactly at the threshold while Payoff remains
8%. That is a limited reading of one opening paragraph, not evidence that the
system design or the rest of its documentation fails. No documentation rewrite
or change to accepted code follows from that score alone.

**The v5 run and its rubric remain frozen.** Before a documentation gate, distinguish
the unit being judged: a slogan can carry a hook; a complete explanation must
make the mechanism traceable. The user's clarification selects separate
judgments for memetic appeal and conceptual value. A successor rubric should
remove substantive value as a prerequisite for memetic appeal while retaining
the separate compression and correctness requirements. Test that change against
these exposed examples and fresh controls. Independently adjudicate labels
before calling a disagreement a false positive. Do not lower thresholds
merely to make these examples pass, and do not claim that cultural popularity
proves compression, technical truth or every other style axis.

## Verification and replay

- **50/50** Score distributions validate through the production validator.
- Every saved request exactly matches the payload generated by the production
  evaluator using the frozen questions; input, rubric, evaluator and runner
  hashes match. All 10 responses resolve to Jev 1.13.0.
- **51/51** focused existing offline style, potential and role tests pass.
  Stubbed tests establish workflow behavior, not taste calibration.
- No Bend sources, rules or thresholds changed. No compiler/backend tests were
  needed for this documentation experiment.

Recheck saved evidence without provider calls:

```sh
node docs/perch-calibration/memetic-prose-2026-09-27/run.mjs verify
```

The recorded run used `run.mjs freeze`, then `run.mjs live`, with the existing
project credential loaded privately through Node's `--env-file` option. The
runner refuses an existing request/response directory to prevent silent rerolls.
Do not delete receipts to run it again; a successor needs its own experiment
identity, frozen expectations and explicit comparison scope.
