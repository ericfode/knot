# Central laws: one bounded presentation trial

**Keep the five equation-layout changes. This is a partial style result, not an
automatic style pass or a new representation.** Every theorem token is identical,
the complete proof file is byte-identical, and the existing compiler gates pass.
The selected laws already met their declaration targets before this change.

## What changed and why

Each selected equation now puts the operation, exact result and Result type on
three successive lines. This makes the two sequencing cases and the three
occurrence cases easier to compare without reading through long constructor
expressions to find the equality. The names and original ordering already express
the desired progression: affine use, erasure preserving identity, then constructor
freshness. No helper, slogan, new vocabulary or additional claim was introduced.

The changed source is [check-LAWS.bend](../../check-LAWS.bend). The original
[law](baseline/check-LAWS.bend.snapshot) and
[proof](baseline/check-PROOF.bend.snapshot) snapshots and the immutable
[candidate](candidate/freeze.json) make the exact comparison recoverable.
[Registration](registration.json) froze 98 source, configuration and independent
gate inputs before the one candidate. There was no compiler-diagnostic retry.

## Correctness and semantic review

[Verification](gates/verification.json) confirms identical lexical tokens for
the complete law file, byte-identical proofs, unchanged unselected law blocks
and all frozen inputs except the authorized layout. All five src proof entry
points return `All terms check.` The unchanged
[checker gate](gates/checker.json) passes 49 reference fixtures, 98 native/Bun
observations, 10 depth observations, 16 catalog-bound observations and seven
type-valid semantic mutants. Only its build and receipt destinations were
redirected; its semantics, expected values and assertions are unchanged.

Targeted semantic review completed 18 checks in six requests/responses through
jev-1.13.0, with no broken selected rule. Ten checks cover the five actual laws;
eight cover the [bounded law packet](../../../research/compiler-style/central-laws-1/LAW_REVIEW.md).
An initial packet invocation under src had zero coverage and sent zero requests.
The unchanged packet was moved to the research prefix selected by the existing
rules. That failed invocation is retained; no rule or selector was changed.

## Style evidence

| Review | All declaration targets | Complete-family Memetic / Anticipation / Payoff |
| --- | ---: | --- |
| Exact baseline family: five laws and five proofs | 5/10 | .24 / .04 / .1212 |
| Exact candidate family: five laws and five proofs | 5/10 | .29 / .04 / .14 |
| Five actual changed source declarations | 5/5 | Expanded whole-file context unavailable |

Both family projections supply the exact five theorem/proof blocks and unchanged
syntax, core and scope modules. Unused checker/frontend imports are omitted only
from the projection. Every selected-family dependency is present, and neither
composition is truncated. Every law meets its current supporting-role targets;
the five unchanged `{==}` proof fills still miss one or more targets. Complete
family targets remain .60 each. Their small probability differences do not
establish an improvement. Original proof bodies remain intact.

The actual-source command separately covers every changed declaration with
complete individual context. Its whole-file expansion includes an unrelated
`no_checker_budget` law whose `K.check` collaborator is outside that group, so
that expanded composition is unavailable. It is not substituted for the complete
selected-family result. Task potential is low under the fixed five-law contract;
Galaxy brain is not required. All other current requirements stay unchanged.

The three style calls completed 28 provider requests/responses under jev-1.13.0;
only the fixed task-potential answer was reused. Full distributions, expressive
roles, hashes and limits are retained in [reviews](outcome.json). No unchanged
source was rerolled for another score.

## Closeout

One candidate is complete. Retain the modest reading improvement and the failed
composition targets together. There is no next candidate in this trial, and its
partial outcome does not block the compiler-pipeline or IntMap experiments.
Integrate only the narrow law/result commit; do not merge the divergent trial
history, policy, driver or package sources. No package publication is authorized.
