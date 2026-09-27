# Memetic appeal is independent of conceptual value

The user clarified that a passage can be **vacuous and memetic**. Version 6
removes conceptual value, usefulness, truth and explanatory substance as
prerequisites for the memetic axis. Its target remains level 3 with 60%
probability mass. All other axes and all target thresholds are unchanged.

The production change is confined to the `highly_memetic` question and its
levels, plus the shared composition instructions that could otherwise reimpose
a substance requirement. Compression, Delight, Anticipation, Payoff, expressive
role and task-potential rubrics remain separate. Catchiness cannot supply an
overall style pass when another required axis fails. Compiler acceptance is
independent as before.

## Human judgment and frozen expectations

In the [original experiment](../memetic-prose-2026-09-27/README.md), the assistant
labeled a rhythmic but vacuous passage as an intended negative. Jev gave it 78%
memetic target mass. The user explicitly rejected the conflation:

> something can be memetid without being valuable.
>
> it's vacous, but it is memetic

That is a positive human label for memetic appeal and a separate judgment of
vacuity. The user did not assign a numeric score. We translate the positive label
into a target expectation for calibration; that translation is the assistant's.
The original model result was not a false positive under this clarified objective.
Old expected labels and responses remain intact.

[cases.json](cases.json) freezes four cases before any v6 review: the exposed
human example, the exposed Go proverb, and two fresh comparison cases.
[freeze.json](freeze.json) pins both policies, every request, the evaluator and
runner. Metadata, labels, authorship, prior results and cultural evidence are
excluded from model input. The same text and purpose are used under both policies.

The fresh positive is **“Colorless green ideas sleep furiously.”** It appears in
an [interview with Chomsky](https://thereader.mitpress.mit.edu/noam-chomsky-interview/)
and an [MIT Libraries retrospective](https://libraries.mit.edu/150books/2011/04/13/1957/).
This is evidence of reuse. Its semantically anomalous wording does not imply that
the example lacks scholarly value. The fresh plain sentence concerns the fields
in a report. Its negative expectation concerns ordinary form, not low utility.
Both fresh labels are assistant hypotheses, not user-adjudicated truth.

## Results

Values are probability mass at level 3 or above. Bold values meet the 60% target.
They are model judgments, not measured probabilities of human transmission.

| Specimen | v5 memetic | v6 memetic | v6 compression | v6 all five |
| --- | ---: | ---: | ---: | --- |
| User-positive vacuous wordplay | **78%** | **99%** | 30% | Below requirements |
| Go shared-memory proverb | **93%** | **93%** | **78%** | Below requirements |
| Colorless green ideas | **76.8%** | **100%** | 34% | Below requirements |
| Plain reporting sentence | 0% | 0% | 32% | Below requirements |

All four v6 judgments meet the recorded expectations. Crucially, the human
example remains low on compression while rating highly on memetic appeal. The
fresh plain sentence remains low despite the permission for vacuous expressions
to be memetic. This small set is consistent with the intended independence;
it does not establish calibration accuracy or broad specificity.

The two exposed v5 results are **exact request-matching reuse** from the earlier
run. The remaining six requests were fresh, serial calls to Jev **1.13.0**.
Neither failed nor repeated. v5 and v6 already agreed on the pass/fail labels in
this set; the change fixes the documented criterion and assistant adjudication,
not a demonstrated model-classification failure. Numerical movements are
descriptive single observations, not statistically established improvements.

All 40 distributions, raw successful responses, request identities, origin
markers and the [v6 rubric snapshot](rubric-v6.json) are preserved alongside
[results.json](results.json). The other questions' small score movements do not
mean their instructions changed; the full request contains a changed memetic
question and the inference is fresh.

## Verification and limits

- **84/84** offline tests plus the eight-law wiring gate pass via
  `npm run lint:verify`. [Output](offline-tests.txt) is retained.
- `lint:rules -- --json` parses successfully.
- **40/40** distributions validate through the production Score validator.
  Each prepared request matches what the production evaluator sends.
- A structural comparison verifies that only policy version, memetic rubric and
  composition instructions differ. All other rubrics and thresholds are equal.
- A high memetic result still fails the five-axis conjunction when compression
  or another required axis fails. No Bend source or deterministic contract changed.

This remains a prose transfer probe through the production evaluator, not a new
Markdown CLI mode or a full Bend qualification. The composition instruction
change is checked for separation and covered by existing offline workflow tests;
it has no new live Bend-composition calibration here. Human taste evidence is one
exposed example. Famous wording can be recognized despite withheld attribution.

Recheck the frozen comparison without provider calls:

```sh
node docs/perch-calibration/memetic-value-v6-2026-09-27/run.mjs verify
```

This verifier uses saved policies, so subsequent policy changes do not rewrite
old ratings. It still checks evaluator and runner identities. New rubric work
needs a new experiment identity and fresh expectations; existing outputs cannot
be silently overwritten or rerolled.
