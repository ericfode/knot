# Symbols and the memetic valley — 2026-09-26

The requested fresh Perch rerun completed. The bounded semantic review reported
no violations, but **none of its 15 implementation declarations
meets all three style targets**. No implementation, rule, rubric, contract,
assertion, published package or shared campaign state was changed.

## Fresh evidence

`npm run lint:style -- --live packages/symbols/main.bend` reviewed all 13 definitions
and two datatypes. Fifteen requests/responses produced 45 ratings with
`jev-1.13.0`; exit 3 correctly means style attention, not provider failure.
Conceptual compression: 13 meet, 2 uncertain. Delight: 3 meet, 9 uncertain,
3 below. Memetic: 0 meet, 0 uncertain, 15 below. Target mass is normalized
probability on levels 3/4; each axis requires at least 60%.

| Declaration | Conceptual | Delight | Memetic | Context |
| --- | ---: | ---: | ---: | --- |
| `Error` | 50% | 41% | 7% | limited |
| `Table` | 71% | 44% | 4% | limited |
| `Table.bounded` | 95% | 62% | 3% | untruncated |
| `Table.new` | 91% | 48% | 2% | untruncated |
| `metadata` | 90% | 52% | 5% | untruncated |
| `Table.length` | 90% | 39% | 3% | untruncated |
| `Table.limit` | 93% | 52% | 3% | untruncated |
| `found` | 91% | 56% | 2% | untruncated |
| `Table.find` | 76% | 31% | 5% | untruncated |
| `inserted` | 85% | 61% | 3% | untruncated |
| `append_name` | 88% | 55% | 8% | untruncated |
| `intern_found` | 76% | 59% | 11% | untruncated |
| `Table.intern` | 55% | 66% | 16% | untruncated |
| `resolved` | 60% | 44% | 2% | untruncated |
| `Table.resolve` | 72% | 32% | 4% | untruncated |

Datatypes have the four-user context cap; function contexts are untruncated.
Remote Vec internals and Base definitions are not resolved by this reviewer.
The highest memetic mass, 16.2% for Table.intern, is still far below 60%.
Every request-state hash and the rubric hash match the prior Symbols baseline;
these were user-requested fresh calls, not changed implementations. Small shifts
are repeated-judgment variation and do not establish independent confirmation.

A fresh bounded semantic pass selected `Table.intern` and `inserted` with
machine-arithmetic, borrow-lifetime, loop-invariant-work and amortized-growth
rules, plus the real LAW_REVIEW packet with eight law rules and the package rule.
Seventeen checks, three requests/responses, no reported findings. No defect was
confirmed, no reported false positive needed adjudication, and no reported
finding remains unresolved. All scores and context limits are retained.

Receipts: [style distributions](receipts/memetic-review-2026-09-26/style.json),
[style usage](receipts/memetic-review-2026-09-26/style-usage.json),
[semantic index](receipts/memetic-review-2026-09-26/semantic-index.json),
[comparison/validation](receipts/memetic-review-2026-09-26/analysis.json).
Current source hashes still match the published Symbols closure and existing
deterministic gates. No source changed, so proof/runtime/mutation suites were
not rerun for an advice-only increment.

## What the valley does and does not show

1. **The utility code has a real local vocabulary problem.** `metadata`, `found`,
   `resolved`, `append_name`, `intern_found`, `inserted` each perform sensible
   work, but the reader sees much generic pair unpacking and repacking. The
   interner's defining idea—one stable position viewed in two directions, with
   a forward entry committed only after reverse append—does not dominate its
   names and visual progression. This is an author's reading diagnosis, not
   a defect or a human preference already confirmed by the user.
2. **The judge's role sensitivity needs calibration.** The historical project
   baseline had five memetic passes among 1,887 declarations: check.run,
   eval.step, parse.run, parse.parse and wasm.lower. No law, proof fill or datatype
   passed. The two-line parse.parse entry passed, so this is not simply a size
   effect. Those files have since changed; these are historical ratings, not
   present acceptance. The pattern suggests that semantic role/context matters.
   It does not establish that the rubric is wrong, nor justify waiving helpers.
3. **More compression has not closed the current pilot.** The owner's latest
   completed task.run receipt has target masses 82% conceptual, 81% delight,
   **52% memetic (uncertain)**. Its matching baseline was 84%, 83%, 57%. The current
   source matches the owner candidate snapshot. I reused that completed receipt
   without another call or an edit outside Symbols. This small score movement
   is insufficient evidence of a taste regression; it does establish that the
   shorter candidate has not met the unchanged pilot bar.

The pilot's current form is:

```bend
def run(fuel: Nat, state: Run) -> Run:
  match fuel state:
    case 1n+n Checkpoint{task}: run(n,step(task))
    case _ _: state
```

It expresses “advance the pending case; otherwise preserve the owner” cleanly.
That concrete gain and the owner's deterministic gates must remain distinct
from memetic acceptance. Making it still shorter is not an evidence-backed next
step. The current pilot remains unresolved, and the wider campaign queue remains
intact; this report does not dispatch another implementation batch.

## Suggested next moves, in order

**1. Establish taste anchors before another broad rewrite.** Select a small fixed
set: two existing excerpts the user wants more of, a correct but generic example,
and an over-styled counterexample. Include a tiny helper and a coherent function
family. Record the user's reasons before review, then ask the unchanged rubric
for all three axes. Keep fresh examples held out. If the human-approved examples
cannot clear the bar, investigate the prompt/context/decision policy explicitly;
do not use repeated scores as a substitute for preference evidence.

**2. Diagnose whether the evaluation unit fits the objective.** Keep every current
declaration rating visible and keep the existing pilot threshold. Separately
review a fixed semantic family with complete bounded context: does a reader learn
a grammar, then recognize it in the next operation? Compare that diagnostic with
the per-declaration results. A projection may carry a family's identity without
being a standalone quotation. If the discrepancy is confirmed, propose a
separately versioned role-aware policy; do not retroactively turn failures into
passes or average away the current all-declaration requirement.

**3. Give Symbols an earned grammar, when its batch is dispatched.** Preregister
one concrete hypothesis around the intern family: `probe → append → commit`.
Those are real transitions, not branding. A hit returns the old ID; a miss obtains
one append position; successful append permits the forward binding; every failure
retains both views. Investigate whether one consistent table/result shape and
stage vocabulary exposes that sequence with less tuple plumbing. Compare the
whole four-function family, not an isolated renamed helper. Keep public API,
allocation order, table lifetime, independent model, accepted laws and all eight
semantic mutations fixed. Reject extra wrappers or affine closure complexity
that add more explanation than they remove. This is a proposed experiment, not
implemented Bend or a promised score gain.

**4. Use one candidate and a stopping rule.** Preserve the frozen baseline and
make one substantive candidate under the campaign's Astra/max procedure. Keep
all unchanged deterministic gates. Score every changed/introduced declaration
once with the unchanged rubric; do not rerun unchanged code for a better draw.
Require a concrete reading benefit as well as gate acceptance. Preserve partial
improvement as partial; if memetic evidence stays low or uncertain, return to the
calibration question rather than adding jargon, punctuation or new abstraction
layers. No threshold reduction, waiver or wider dispatch is proposed while the
current pilot is unresolved.

The practical first move is the anchor/context diagnostic. It can distinguish
“our vocabulary lacks a hook” from “we are requiring each support declaration to
have an independent cultural identity.” Both explanations may contribute; the
current receipts alone cannot apportion them.
