# Compiler pipeline trial 1

**Disposition: keep the small readability improvement; partial style result.**
The one candidate passed its first compiler check, all five existing suites and
20 direct IO observations. It does not meet the memetic objective, and it does
not receive automatic style qualification. The broader compiler goal remains
paused. This trial authorizes no further candidate or component sweep.

## What changed and why

Before, the reader followed `source` into `parsed` to discover that checking was
the third stage. The revised `source` contains tokenize, parse and check together;
two uses of the existing `syntax.bind` carry the same first-error rule, and the
outer `checked` call exposes the final IO boundary.

```bend
def source(+limits: Limits, text: String, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits:
    case Limits{chars,+parser,+checker}:
      checked(
        S.bind(List<&2,S.Token>,C.Book,L.tokenize(chars,text),tokens =>
          S.bind(P.Parsed,C.Book,P.parse(parser,tokens),tree =>
            K.check(checker,parsed_root(tree)))),
        next)
```

The new `parsed_root` projection accommodates the seed's parameter-only matching
rule and makes the existing disposal of residual tokens explicit. Public
`parsed` preserves its independent entry behavior. The tradeoff is a small helper
and repetition of the root/check expression in the two public paths. That cost
is justified here by keeping the primary pipeline visible in one expression.
No new datatype, protocol, imported abstraction or loop was introduced. This is
an author's reading judgment; the user has not supplied a blind preference.

[The complete baseline](baseline-driver.bend.snapshot), [first candidate](candidate-first.bend.snapshot)
and [author notes](author-notes.md) are preserved. The parsed
[declaration diff](declaration-diff.json) confirms only `parsed` and `source`
changed and `parsed_root` was added. All ten other declarations, including
`Limits`, `checked`, file IO and argument helpers, are byte-identical.

## Fixed experiment and acceptance

[SPEC.md](SPEC.md) records the pre-generation contract and reading hypothesis.
[freeze.json](freeze.json) freezes 191 inputs at `4a1c245`, including source,
contracts and all existing test bodies/manifests. Author: GPT-6 Astra, max.
One substantive generation; zero compiler-diagnostic retries.
[The first compiler receipt](receipts/first-compiler.json) retains the exact
success and seed update notice. The notice did not change the pinned toolchain.

| Gate | Fresh candidate result |
| --- | --- |
| Frontend | 14 reference fixtures, 24 boundary observations, 4 semantic mutants |
| Checker | 49 fixtures, 98 checked observations, 10 depth and 16 catalog-bound observations, 7 mutants |
| Wasm | 25 programs, 90 independent reference calls in two lanes, 64 rejection pairs, 44 boundaries, 7 mutants |
| Fields | 40 fixtures, 240 phase observations, 36 budget probes, 6 host probes, 12 level/inspection observations, 9 mutants |
| Structural catalog | 16 fixtures, 4 boundary pairs, 7 mutants |
| Direct driver IO | All 10 frozen cases pass in native and Bun: 20 observations, both before and after |
| Complete proofs | All five existing proof entry points return `All terms check.` |
| Emitted modules | All 25 candidate Wasm modules equal the freshly generated baseline byte for byte |

[verification.json](verification.json) records gate receipt hashes, frozen input
comparisons and every module hash. Only `src/driver.bend` changed among frozen
inputs used by these gates. The 34 mutants and all existing assertions remain
unchanged. No universal driver-equivalence proof, whole-compiler bootstrap,
GPU execution or performance improvement is claimed. IO witnesses measure
sequence and multiplicity, not elapsed timing. This trial adds no repeated
stage traversal; constant-factor compiler-host overhead was not benchmarked.

The direct witnesses fill a real gap: the existing parser/checker CLIs implement
their own adapters and do not call this driver. The Wasm, fields and structural
suites exercise it. [witnesses.json](witnesses.json) adds fixed success, error
category/location/status, residual-token, independent-budget and callback-order
observations. Host scripts only invoke Bend and compare literal expectations.

Replay commands are recorded in receipts. `run-gate.py` imports unchanged test
modules and redirects only build/receipt/generated destinations. Historical
receipts and deliberate generated examples are untouched. Receipts are immutable;
replay a frozen checkout in a separate evidence destination rather than replacing
this record. Local build products are ignored and are not part of the commit.

## Semantic and style review

Targeted Perch completed four selected rules on each changed declaration:
12 checks, no reported findings. Full rule probabilities are in
`receipts/candidate-semantic-*.log`. `parsed` and `source` had truncated dependency
contexts; the projection did not. This is bounded advisory review, not proof.
The [law packet](LAW_REVIEW.md) distinguishes theorem and finite-observation
claims. Its attempted review returned zero coverage because the installed law
selectors do not include `src/**/LAW_REVIEW.md`. The wrapper correctly failed;
[the attempt](receipts/law-packet-review.log) is unavailable evidence, not a pass.
No rule or selector was changed within this source-owner trial.

Normal v5 style review used fixed task evidence and `jev-1.13.0`. The task-only
potential-profundity judgment was low (0% at the relevance threshold) and reused
unchanged for the candidate. No Galaxy requirement was added. Full distributions,
context bounds, source/helper hashes and model identity remain in
[baseline-style.json](receipts/baseline-style.json) and
[candidate-style.json](receipts/candidate-style.json).

All selected declaration compression and delight targets are met. Every memetic
target is below threshold. `parsed` and `source` have unavailable Anticipation
and Payoff due to truncation. The normal composition review is unavailable due
to unresolved imported context and the composition byte limit. The supplied
role probabilities favor supporting `checked` and `parsed_root`, but unresolved
role context causes the tool to keep their role uncertain and apply level 3.
Those actual classifications are retained; they are not manually converted into
passes. `parsed` remains uncertain; `source` is leading.

A [supplementary bounded protocol](bounded-review-protocol.json) supplies every
local pipeline declaration and explicit opaque interfaces for the unchanged
compiler stages. It retains the same rubrics and sees one revision per request.
The [baseline](receipts/baseline-family.json) and [candidate](receipts/candidate-family.json)
are conditional reading evidence only; they cannot replace unavailable normal
composition or declaration coverage.

| Bounded family axis | Baseline target mass | Candidate target mass |
| --- | ---: | ---: |
| Compression | 74% | 78% |
| Delight | 84% | 85% |
| Memetic identity | 14% | 18% |
| Anticipation | 5% | 6% |
| Payoff | 13% | 14% |

The small family differences are weak preferences, not established improvement
in reader response. The source-level readability gain has a concrete explanation
above; the memetic gap remains. Routine pipeline composition supplies little of
the project's distinctive vocabulary by itself. There is no reason to add more
machinery or rename correct code to chase these scores.

## Handoff

This trial is complete as a kept, deterministically verified revision with style
debt and review limits. The shared campaign coordinator owns consolidation and
any rubric/context follow-up. The immutable inputs, first candidate, first
compiler result, before/after observations and every review remain here. Other
owners' library and checker-law changes were left untouched. Find the source
checkpoint with `git log -1 -- src/style-campaign/compiler-pipeline-1/STYLE_CAMPAIGN.md`.

After this trial's frozen gate window closed, the separate law trial integrated
as `e5a7f38`. [handoff.json](handoff.json) records that chronology. Its five-law
layout change has independently identical non-whitespace bytes to this trial's
frozen law source. The law owner reported the combined checker proof passing;
the historical pipeline gate receipts were not rewritten or rerun for whitespace.

Per-declaration target masses follow; `n/a` means unavailable, never zero.

| Revision / declaration | Compression | Delight | Memetic | Anticipation | Payoff |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline / `checked` | 99% | 89% | 1% | 0% | 1% |
| baseline / `parsed` | 97% | 79% | 3% | n/a | n/a |
| baseline / `source` | 79% | 64% | 6% | n/a | n/a |
| candidate / `checked` | 99% | 87% | 1% | 0% | 1% |
| candidate / `parsed_root` | 100% | 66% | 0% | 0% | 2% |
| candidate / `parsed` | 97% | 76% | 5% | n/a | n/a |
| candidate / `source` | 90% | 84% | 16% | n/a | n/a |
