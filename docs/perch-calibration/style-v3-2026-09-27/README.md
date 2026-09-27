# Perch rubric v3 integration evidence

Run on 2026-09-26 Pacific / 2026-09-27 UTC. This increment installs the
user-approved memetic refinements and separate Anticipation and Payoff scales.
The user's final policy requires both for anything marginally critical.

## Installed policy

- Keep the three primary style targets and the existing Galaxy-brain target for
  critical or uncertain functions, laws and proofs.
- Classify every declaration, including datatypes. A supporting material role in
  a contract qualifies; uncertain classifications cannot select the lower bar.
- Require Anticipation 3 (Inviting) and Payoff 3 (Earned), each with at least 60%
  probability, for critical or uncertain declarations. Noncritical declarations
  retain both as advisory ratings. Scores do not compensate for one another.
- Withhold both numeric diagnostic questions when bounded context is truncated.
  Record unavailable evidence and prevent an automatic pass.
- Preserve full distributions, context limits and rubric identities. Campaign
  inventory checks include every applicable target, including through their
  conservative legacy field alias.

## Deterministic verification

`npm run lint:verify` passed **35 tests** and the **eight-rule law wiring gate**.
The tests exercise critical, noncritical and uncertain classifications; exact
probability boundaries; independent diagnostic requirements; datatype policy;
truncated context; malformed/missing answers; changed-rubric reuse; provider
failures; and campaign pass accounting. These are enforcement checks, not model
calibration. `npm run lint:rules -- --json` loaded **27 enabled custom rules**.

No Bend implementation changed in this increment. Compiler, proof, backend and
performance experiments were not rerun for this configuration change.

## Bounded live check

[Preflight](preflight.json) records the reading-role hypotheses, source/context
hashes and expected request coverage before dispatch. [Live receipt](live.json)
retains all responses. The rubric SHA-256 is
`54cbef848b22aba58ab494b77b96f5c75832984ac4a8dbc2e8f8dc7223b65e40`.

```sh
npm run lint:style -- --live \
  src/scope.bend::alternatives src/scope.bend::Scope \
  tests/perch-style/a.bend::solve \
  --output=docs/perch-calibration/style-v3-2026-09-27/live.json
```

Three requests to `jev-latest`, resolved as `jev-1.13.0`, returned all **16
expected Score answers**: six for each function and four for the truncated
datatype. Coverage was 3/3 with current source/context hashes. The command
returned **3 (style attention)**, not a provider failure or a style pass.

| Declaration | Critical probability | Anticipation P(level ≥3) | Payoff P(level ≥3) |
| --- | ---: | ---: | ---: |
| `src/scope.bend::alternatives` | 98% | 32%, below target | 54%, uncertain |
| `src/scope.bend::Scope` | 100% | Unavailable: truncated context | Unavailable: truncated context |
| `tests/perch-style/a.bend::solve` | 78% | 21%, below target | 11%, below target |

All three received the conditional requirements. The datatype retained its
ordinary big-brain target; both functions received the Galaxy-brain target.
Across 15 required assessments, 2 met target, 10 were below target, 1 was
uncertain and 2 were unavailable. **No declaration passed all requirements.**
The two rated functions retained unresolved-reference warnings, including
built-ins; their diagnostics are explicitly marked `limited_context`.

## Disposition and limits

**Integration verified; taste and criticality calibration remain open.** The
two scope declarations matched the preregistered critical-role expectations.
The illustrative list-map fixture did not: the model assigned 78% criticality
despite the preregistered noncritical role expectation. Retain this as an
unresolved classification disagreement. Do not rewrite the fixture, change its
label in the receipt or weaken the threshold to manufacture agreement.

Future calibration should supply explicit role/contract context and compare
fresh critical and incidental controls with human judgments recorded first.
Include earned confirmation, earned surprise, weak preparation, flat resolution
and unnecessary delay. This bounded check establishes live wiring and gate
behavior only. It does not establish human preference agreement, statistical
independence of the scales or an improvement over older rubric versions.

Historical campaign receipts remain historical. A new rubric hash requires a
new baseline or an explicitly recorded transition; earlier passes cannot be
relabeled as v3 passes. Keep independent semantic and performance gates fixed.
