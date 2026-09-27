# Task-only potential controls

These five inputs exercise `potential_profundity` in Perch style policy v4.
They contain task obligations and observable contracts, with no implementation,
author identity, rating instructions or desired classification. Supply only a
control text to the source-blind task API. Do not send this README or
expectations.json as model input.

The [expectations](expectations.json) are assistant-origin preregistrations,
recorded before any live rating. They operationalize the requested contrast and
are neither an independent human panel nor known objective ground truth. The
policy and input hashes identify exactly what was anticipated. No provider call
was made while preparing these files.

| Stage | Task | Expected relevance |
| --- | --- | --- |
| Development | [D01](D01.task.md): four-character hexadecimal conversion | Not relevant |
| Development | [D02](D02.task.md): labelled-path queries | Relevant |
| Held out | [H01](H01.task.md): shipment-row validation | Not relevant |
| Held out | [H02](H02.task.md): changing multiset queries | Relevant |
| Hypothesis probe | [P01](P01.task.md): bounded Conway Life | Open |

D01's two directions are fully determined by place values and a fixed alphabet.
H01 has multiple checks and a conditional dependency, but its requested result
is still independent row bookkeeping. Their length and edge cases do not imply
an opportunity for a deeper organizing principle.

D02 requires the same path contributions to survive several interpretations,
cycles and replacement of subgraphs by boundary summaries. H02 requires static
multisets, signed changes and occurrence explanations to agree through composed
queries. These are explicit compatibility obligations between representations,
not an inference from workload, importance, speed or unfamiliar terminology.
A relevance expectation does not assume a successful implementation, a novel
algorithm, or any particular solution. A model disagreement remains evidence.

Rate and interpret D01/D02 first. Keep H01/H02 and their expectations byte-identical
after development interpretation; do not rewrite them in response to that result.
Then rate H01/H02 once with the frozen policy. A mismatch or uncertain result is
retained, not tuned away. Provider failures are unavailable observations rather
than disagreements. Assess both the absolute class and the ordered high/low
contrast; a relative preference cannot substitute for the required target mass.

P01 is outside the four-control success denominator. The user's suspicion that
Life may have limited conceptual opportunity is a hypothesis to measure, not a
label. Local neighborhood structure and repeated evolution could support useful
composition; the bounded stepping contract also omits broader research questions
about the system. Neither the domain's fame nor earlier implementation outcomes
should determine the rating. Preserve its complete distribution and report
relevant, not relevant, or uncertain without using it to tune this rubric.

P01 transcribes the behavior, interface and language restrictions of the fixed
Life experiment contract, excluding historical author settings and style policy.
Its explicit non-goals only clarify the original bounded operation. The source
contract's path and hash are recorded in expectations.json. No prior candidate,
score, decoded inducer or experimental result is included in any task text.

These controls test a narrow intended distinction. Even separation on all four
would not establish general calibration or validate every task-level threshold.
The root operator owns live receipts, interpretation, policy promotion and Git.
