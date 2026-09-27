# Provisional reading observations: T007, T003 and T006

Updated 2026-09-27 at 04:37 UTC while R2 was running. This bounded reading covers
all three completed rounds of **three trajectories**, not the final 30-trial
campaign. T007 (`w1-n3`) and T003 (`w1-n1`) used GPT-6 Astra/low; T006 (`w1-n2`)
used GPT-5.6 Sol/xhigh. No no-inducer sample is included. These observations are
for reporting, not author feedback. No code, rubric, prompt or receipt was
changed or rerun.

The source snapshots match their saved behavior and review source hashes. All nine
have passing finite behavior receipts (1,537 fixtures plus 21 composition checks
on each of Node and Bun; 28 native fixtures) and clean source review, totaling
220 rule checks. T003 round 3 needed its one compiler repair; the other eight
passed their first compiler check. All nine finished with style attention and no
full pass. Those are recorded gate outcomes, not new correctness proofs.

## Evidence set and saved model outcomes

The [unchanged v3 rubric](../../perch-style.json) has SHA-256
`54cbef848b22aba58ab494b77b96f5c75832984ac4a8dbc2e8f8dc7223b65e40`.
Each style receipt is completed, reports current source and untruncated contexts,
and records observed judge `jev-1.13.0`. There were 56 provider responses for 56
declaration visits and zero reused rows. Contexts still report 1–14 unresolved
references; untruncated does not mean every imported/builtin definition was seen.

| Trajectory / round | Reviewed source | Source SHA-256 | Required assessments met | Saved distributions |
| --- | --- | --- | --- | --- |
| T007 / 1 | [first](trials/T007/round-01/first.bend.snapshot) | `38b3ca1a1edcb631759e89350d524c2bf98844b9211fdb16ba041910e4e11f8f` | 7/35 | [style](trials/T007/round-01/style.json.gz) |
| T007 / 2 | [first](trials/T007/round-02/first.bend.snapshot) | `5710872874325ec76f1d60e19561b4e4533a30c3d435ca12e817f8364b3a2e15` | 11/30 | [style](trials/T007/round-02/style.json.gz) |
| T007 / 3 | [first](trials/T007/round-03/first.bend.snapshot) | `850392eda4d1a5be132ea36c03b9c39e52715157cbc6efc5f675e3dcb0de8d22` | 11/30 | [style](trials/T007/round-03/style.json.gz) |
| T003 / 1 | [first](trials/T003/round-01/first.bend.snapshot) | `3894d5f31df8562fa0d6a867aa5122cf64afcab57ed46e9cc4afd5c4e178d188` | 7/30 | [style](trials/T003/round-01/style.json.gz) |
| T003 / 2 | [first](trials/T003/round-02/first.bend.snapshot) | `9eae47792f345ed52de93df541d395e2f6fcf3328a556379ede03e0568b0b2c7` | 13/30 | [style](trials/T003/round-02/style.json.gz) |
| T003 / 3 | [repaired](trials/T003/round-03/repaired.bend.snapshot) | `9509f0e6ec5300d034040738e627d9ce538e5b07d62d04806e258175748e3f1c` | 14/40 | [style](trials/T003/round-03/style.json.gz) |
| T006 / 1 | [first](trials/T006/round-01/first.bend.snapshot) | `5c72f9d80f880b5de010102b7cd27952ba27407621c58590116052d4b0f2b6eb` | 12/30 | [style](trials/T006/round-01/style.json.gz) |
| T006 / 2 | [first](trials/T006/round-02/first.bend.snapshot) | `3b2fcc92020bfa389a49d0ee5009cb23cf432efe2f061e8128a4bbe3f3a4fa18` | 9/20 | [style](trials/T006/round-02/style.json.gz) |
| T006 / 3 | [first](trials/T006/round-03/first.bend.snapshot) | `13cd68c17f56f12df997035c083aa72ed35bc639c7635a1d785f1e14bd1df93f` | 23/35 | [style](trials/T006/round-03/style.json.gz) |

Round-level gate dispositions and source indexes are retained in
[T007 result](trials/T007/result.json), [T003 result](trials/T003/result.json) and
[T006 result](trials/T006/result.json).
This table counts required assessments, not passed declarations: **zero of the
56 declaration visits meets every required target**. Repeated declarations
across rounds are related observations, not 56 independent examples.

| Required dimension | Meets | Below target | Uncertain | Unmet / required |
| --- | ---: | ---: | ---: | ---: |
| Big brain, conditional target | 1 | 55 | 0 | 55/56 |
| Anticipation | 7 | 15 | 34 | 49/56 |
| Payoff | 23 | 11 | 22 | 33/56 |
| Memetic | 26 | 18 | 12 | 30/56 |
| Delight | 50 | 0 | 6 | 6/56 |

There are no unavailable assessments in this set. The table preserves the
difference between below-target and uncertain distributions; both prevent a
full pass. Its denominator is this nine-round evidence set, not all R2 output.

## Routine helpers and the v3 acceptance boundary

**Recorded model result:** all 56 declaration visits are classified critical,
with probability 0.99–1.00. This includes `head0`, the new `mass0`, ordinary
recursive row traversal, packing/unpacking and the `step`/`evolve` wrappers.
The 55 function visits therefore require level-5 probability of at least 0.60.
All miss it: 49 record zero in the returned rounded distribution, and the other
six (all from T006 round 3) record 0.01–0.06. T003/T007's 38 function visits all
record zero.

The sole passing big-brain assessment is T003 round 3's `Column` datatype:
it is critical with probability 1.00 but retains the datatype's ordinary level-3
big-brain target, which it meets with 0.83 mass. Its memetic, anticipation and
payoff targets remain uncertain. The datatype exception does not create a full
pass or exempt its helper functions from level 5.

**Editorial judgment:** the criticality classifications fit the current broad
definition: zero-default sampling implements the dead exterior, and `evolve`
determines exact iteration. Smallness is explicitly not grounds for exemption.
At the same time, a direct list-head default can be exact and pleasant without
revealing the surprising cross-task reframing described by level 5. The rubric's
ordinary level-3 allowance for a well-chosen tiny operation does not override its
conditional level-5 acceptance requirement. These receipts show the consequence
of that policy on routine material helpers; they do not prove either erroneous
classification or that a future implementation cannot satisfy the policy.

## Source reading: actual changes and tradeoffs

The following are my editorial observations from the saved code, separate from
the model probabilities. T003/T007's initial programs expose the same useful
idea: a separable three-by-three sum that includes the center. Life then becomes
`total == 3 || (alive && total == 4)`. T007 sums horizontally then vertically;
T003 sums vertically then horizontally. That relationship and the dead halo are
traceable in the mechanism. I find it a compact explanation of this task; the
samples do not themselves exhibit the additional surprising connection demanded
by the level-5 wording.

**T007, round 1 → 2:** `rows` and its intermediate list of rows disappear.
The new `sweep(fuel,width,cells,above,here)` carries the previous horizontal sums,
computes `below`, then advances `(above,here)` to `(here,below)`. In round 1,
`sweep` recomputes a row's horizontal sum after already computing it as the prior
row's `below`. The revision exposes reuse and the window invariant in the
arguments. Its additional parameters make the signature longer, but they state
the state being advanced. This is a substantive structural change.

**T007, round 2 → 3:** `resolve` takes a `suffix`, returns it at the empty case,
and prepends updated cells to it. `sweep` passes its recursive result directly
instead of calling `List.append` on an intermediate output row. This fuses the
source-level construction and concatenation. The extra parameter requires the
reader to understand the continuation of the result; the base case makes that
convention explicit. `head0` also becomes a direct two-case match. These are
local mechanism changes, without a new Life representation. No allocation or
speed measurement here establishes that the backend realizes a performance gain.

**T003, round 1 → 2:** `head0` becomes a direct match, and `sweep` destructures
the cell and mass lists together. This exposes their alignment but introduces
an explicit nonempty-cells/empty-masses branch returning `Nil`. That branch is
unreachable when `columns` supplies one mass for each middle cell; the reader
must still carry the alignment argument. Names stay stable, and the Life algebra
is unchanged. This is modest structural cleanup with revised invariant comments.

**T003, round 2 → 3:** `Column{cell,mass}` packages each original cell with its
vertical population. `sweep` now consumes one stream, so list-length alignment
no longer depends on coordinating two separate lists. The datatype does not
prove that a mass was computed correctly; `columns` still establishes that
relationship. This is the strongest representation improvement in T003, in my
reading: it removes an internal mismatch case. It also adds a datatype and,
after the compiler repair, `mass0`. The [diagnostic](trials/T003/round-03/compiler-first.json)
rejects destructuring a computed value; the repair introduces a helper that
matches its parameter. That compiler-motivated helper receives its own critical
level-5 target. This illustrates a concrete interaction between legal Bend
decomposition and the per-declaration acceptance policy.

**T006, rounds 1 → 2:** the initial program scans the complete old board for
each output cell. `Life.halo` gives the coordinate neighborhood, `Life.census`
counts it, and `Life.fate` applies B3/S23. Round 2 folds these into `Life.vote`,
includes the center and uses `total == 3 || total == 3 + alive`. It also removes
product fuel from a traversal already bounded by the input list. The algebra is
simpler, but the lengthy coordinate predicate is duplicated across two row-clock
branches. I read this as a mixed presentation change: fewer declarations do not
automatically mean less work for the reader.

**T006, round 2 → 3:** this is a different representation, not a retelling of
the coordinate scan. `Life.pack` puts one row in a U32; `Life.eight_winds` lays
out the shifted north/center/south masks as three visual rows with the center
missing. The name and layout carry actual geometry. `Life.quorum` accumulates
the eight masks into `ones`, `twos`, `fours` bitplanes using XOR and carries,
then selects `twos & ~fours & (ones | alive)`. Two neighbors require the old cell;
three do not. Eight wraps the low three count planes to zero and is rejected.
The comment explaining that last case helps the reader verify why a fourth
plane is unnecessary. This is an earned relation between the word representation,
geometry and Boolean decision, in my reading.

The boundary mechanism still matters: a zero row is supplied above and appended
below; `unpack` returns only the requested width and cell count. Each next public
step repacks that clipped board. Thus any unused high lanes of a narrow row are
not persistent exterior state. Packing/unpacking introduce their own row-clock
bookkeeping, and `sweep` still has an explicit mismatched-stream branch. The
source replaces per-cell world scans with a pack/word-sweep/unpack organization;
this note contains no benchmark, allocation measurements or speedup claim.
Bit parallelism alone does not establish backend performance.

Across these trajectories, **the revisions are more than renaming or comment
churn**. T003/T007 retain their main algebra while carrying a window state,
fusing output construction, or packaging aligned data. T006's third round
changes the representation and decision mechanism. Comments usually explain
those conventions. Structural improvement in this editorial sense does not
establish a higher model score or a passed requirement.

## Score movement is not a reading experiment

T007's `sweep` memetic target mass rises 0.43 → 0.68 → 0.74; its payoff mass rises
0.61 → 0.65 → 0.73. These saved distributions align with my reading of a clearer
moving window and result construction, but no controlled test attributes those
changes to a particular edit. Every T007 anticipation assessment remains unmet.

T003's third round improves alignment structurally while its aggregate required
fraction falls from 13/30 to 14/40. Added declarations change the denominator and
introduce new requirements. Its `columns` anticipation mass rises 0.43 → 0.61,
while `sweep` payoff falls 0.64 → 0.58. There is no uniformly rising score story.

Within T003 and T007, the complete `evolve` definition is byte-identical
across all three reviewed sources. T007's memetic mass for it nevertheless rises
0.49 → 0.69 → 0.79. Its supplied helpers/context changed and each receipt used
fresh responses, so these are not unchanged-prompt repeats. The observation
cannot distinguish contextual judgment from provider variability, and cannot
credit an edit to the body of `evolve` that never happened.

T006's packed version meets 23/35 requirements: delight 7/7, memetic 6/7,
anticipation 4/7, payoff 6/7, big brain 0/7. For `Life.quorum`, target masses
are 0.02 at big-brain level 5, 0.98 delight, 0.85 memetic, 0.78 anticipation and
0.87 payoff. For `Life.eight_winds` they are 0.02, 0.96, 0.89, 0.76 and 0.81.
These two mechanisms clear every requirement except Galaxy-brain. This supports
the narrower observation that the judge can reward their readable geometry and
Boolean organization while rejecting the strongest conceptual criterion. It
does not certify that my reading is correct or that packed rows cause the score
change; the samples, programs, contexts and author histories differ.

These samples support a narrow conclusion: meaningful source-level refinement
can coexist with broad delight acceptance and persistent v3 rejection, dominated
here by critical-function level 5 and anticipation. They do not establish an
inducer effect, a model comparison, human memorability or dopamine, performance,
universal correctness, or the final campaign's pass rate. Two Astra trajectories
and one Sol trajectory with different stimuli do not isolate either model or
stimulus effects. They were chosen for this reading, not randomized into a
controlled comparison. Authors'
stimulus-based hypotheses are hypotheses, not causal evidence. Campaign-wide
counts and any selected-versus-control comparison remain provisional until the
final receipt inventory is complete.
