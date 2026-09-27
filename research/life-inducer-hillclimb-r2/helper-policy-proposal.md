# Proposal: judge supporting definitions by their role

The user raised a different standard for helpers after the first-wave report.
This is a policy proposal, outside the frozen experiment. It changes no current
rubric, score, selection, author prompt or acceptance receipt.

## Separate the questions

Correctness criticality asks what a defect can break. Expressive role asks where
the implementation's central idea lives. A zero-default list head can be critical
to the dead-boundary contract while its best implementation is conventional.
The first wave classified all 173 reviewed declaration visits as critical and
required Galaxy brain on every function, including ordinary adapters.

| Review unit | Proposed expectation |
| --- | --- |
| Core representation or algorithm | Galaxy-brain target; an identifiable, traceable central insight |
| Supporting helper, projection or adapter | Level-3 conceptual economy and readability; exact conventions and a consistent vocabulary |
| Complete collaborating family | Coherent memetic identity, anticipation and payoff across the composition |

Every role keeps identical deterministic and semantic correctness obligations.
A helper should explain more than it adds, have an exact local contract, expose
its invariant, and make the core easier to trace. Padding it with novelty or
ornamental names should lower its assessment rather than help it qualify.

## Role assignment and anti-evasion controls

Assign roles before seeing quality scores, with a short source-grounded reason.
Visibility, call count, definition size and the author's word "helper" do not
establish a supporting role. A private function containing the neighbor-count
mechanism is still core. A public adapter can still be support.

The review must identify the core and its complete relevant family. Moving the
algorithm behind an adapter cannot reduce the requirements on that mechanism.
Inlining or splitting a conventional helper should not cause an arbitrary
acceptance cliff. A role judgment should retain uncertainty for manual review
when the supplied context cannot establish the distinction.

Calibration should include clean and deliberately obscure helpers, an algorithm
mislabelled as a helper, split/inlined equivalents, and a fresh held-out family.
Human reading preferences should be recorded before model review. Revised
helper or whole-family questions need new calibration; old distributions cannot
be relabelled as answers to different questions.

## What current evidence can establish

This proposal addresses an observed mismatch between routine supporting work
and a demand for exceptional originality. It is not a confirmed judge defect.
It also does not automatically qualify the current leading source: T004 round
3's `life` polynomial has only 0.0404 probability on Galaxy brain, below 0.60.
Its other four functions also miss that target. Whole-family judgments have
not been collected, so an emergent family-level pass remains unknown.

Any later policy experiment must use a separate version and report alongside
the original v3 outcomes. The first-wave results remain zero full passes.
