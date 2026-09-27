# TermStore three-axis style scores — 2026-09-26

The earlier parsed Perch report contained semantic and law checks, not style ratings.
This follow-up makes the existing three-axis ratings visible for all **51 declarations**
in `main.bend`: 44 definitions and seven datatypes. **No declaration meets all three
automatic targets.** The implementation and published source are unchanged.

## Evidence and interpretation

All 51 rows were reused from the project review at `2026-09-26T23:43:58.559Z`,
resolving to `jev-1.13.0`. The command below freshly verified source, request state,
helper context, parser, rubric and requested-model identities. It completed with
**51/51 ratings, 153 axis answers, zero new provider requests**, and exit **3**
(style attention). Source freshness is `current`. These are reused model ratings,
not fresh model judgments or human acceptance.

```sh
npm run lint:style -- --live packages/term_store/main.bend \
  --reuse=docs/perch-calibration/style-project-2026-09-26.json.gz \
  --output=packages/term_store/evidence/style-review-2026-09-26.json.gz
```

- [Full distributions, identities and context limits](evidence/style-review-2026-09-26.json.gz).
- Original project receipt: `docs/perch-calibration/style-project-2026-09-26.json.gz`.
- Local verification receipt: `.perch/usage/2026-09-27T02-21-38.786Z-be583b0e-efb5-4e9b-9119-585a2d1076a2.json`.

Each percentage below is the normalized probability at rubric **level 3 or 4**.
At least 60% meets the target; at most 40% is below; the interval between is
uncertain. The memetic score is the distribution mean on the **0–4 scale**.
No package-level mean substitutes for each declaration meeting its own bar.

| Axis | Meets | Below | Uncertain |
| --- | ---: | ---: | ---: |
| Maximally big brain | 47 | 3 | 1 |
| Delightful to read — high dopamine | 35 | 4 | 12 |
| Highly memetic | 0 | 50 | 1 |

## Every declaration

`†` marks truncated context: five datatypes hit the direct-user context bound.
All 44 function contexts are untruncated. Base identities and nonlocal Vec
dependencies remain unresolved as recorded; parsing does not establish typing.

| Declaration | Big brain P(3+) | Delight P(3+) | Memetic mean /4 | Memetic P(3+) | Memetic status |
| --- | ---: | ---: | ---: | ---: | --- |
| [Id](main.bend#L4) † | 86% | 41% | 1.39 | 4% | below target |
| [Error](main.bend#L7) † | 34% | 49% | 1.70 | 11% | below target |
| [Scopes](main.bend#L15) † | 84% | 71% | 1.83 | 12% | below target |
| [Store](main.bend#L18) † | 71% | 47% | 1.53 | 7% | below target |
| [Cell](main.bend#L21) | 83% | 75% | 1.78 | 10% | below target |
| [Action](main.bend#L27) | 71% | 78% | 1.91 | 17% | below target |
| [Memo](main.bend#L34) † | 73% | 54% | 1.82 | 14% | below target |
| [Scopes.from](main.bend#L37) | 97% | 46% | 1.05 | 0% | below target |
| [claim_fresh](main.bend#L40) | 71% | 67% | 1.60 | 5% | below target |
| [make_store](main.bend#L47) | 94% | 72% | 1.39 | 2% | below target |
| [vector_error](main.bend#L54) | 16% | 26% | 1.18 | 0% | below target |
| [Cell.step](main.bend#L65) | 23% | 76% | 1.96 | 18% | below target |
| [Cell.result](main.bend#L92) | 50% | 57% | 1.60 | 7% | below target |
| [make_memo](main.bend#L103) | 94% | 73% | 1.24 | 1% | below target |
| [metadata](main.bend#L110) | 87% | 44% | 1.37 | 4% | below target |
| [snapshot_done](main.bend#L114) | 91% | 53% | 1.29 | 2% | below target |
| [memo_wrap](main.bend#L118) | 97% | 83% | 1.70 | 10% | below target |
| [Scopes.new](main.bend#L122) | 96% | 41% | 1.07 | 0% | below target |
| [claim_available](main.bend#L125) | 91% | 76% | 1.74 | 10% | below target |
| [Store.length](main.bend#L132) | 82% | 32% | 1.50 | 6% | below target |
| [Store.limit](main.bend#L137) | 85% | 34% | 1.44 | 4% | below target |
| [mapped](main.bend#L142) | 86% | 55% | 1.39 | 2% | below target |
| [allocated](main.bend#L149) | 92% | 74% | 1.49 | 3% | below target |
| [Store.snapshot](main.bend#L156) | 77% | 31% | 1.49 | 5% | below target |
| [memo_observed](main.bend#L161) | 87% | 55% | 1.41 | 3% | below target |
| [new_claimed](main.bend#L168) | 91% | 58% | 1.45 | 4% | below target |
| [memo_new_done](main.bend#L172) | 95% | 77% | 1.33 | 2% | below target |
| [Scopes.claim](main.bend#L176) | 88% | 73% | 1.72 | 10% | below target |
| [alloc_pushed](main.bend#L181) | 94% | 78% | 1.77 | 11% | below target |
| [observed](main.bend#L185) | 93% | 74% | 1.72 | 9% | below target |
| [memo_result_done](main.bend#L189) | 96% | 74% | 1.54 | 6% | below target |
| [Store.new](main.bend#L192) | 84% | 79% | 1.94 | 21% | below target |
| [get_scoped](main.bend#L195) | 83% | 80% | 1.85 | 14% | below target |
| [set_scoped](main.bend#L202) | 85% | 85% | 1.83 | 13% | below target |
| [alloc_length](main.bend#L209) | 90% | 69% | 1.78 | 14% | below target |
| [Store.alloc](main.bend#L213) | 69% | 65% | 1.95 | 21% | below target |
| [Store.get](main.bend#L218) | 71% | 77% | 2.04 | 24% | below target |
| [Store.set](main.bend#L225) | 66% | 71% | 2.06 | 25% | below target |
| [Memo.new](main.bend#L232) | 73% | 82% | 1.80 | 16% | below target |
| [Memo.alloc](main.bend#L235) | 80% | 79% | 1.94 | 21% | below target |
| [Memo.inspect](main.bend#L240) | 84% | 67% | 1.73 | 12% | below target |
| [memo_commit](main.bend#L245) | 85% | 83% | 1.67 | 7% | below target |
| [Memo.result](main.bend#L252) | 70% | 70% | 1.80 | 16% | below target |
| [memo_stepped](main.bend#L256) | 92% | 60% | 1.43 | 5% | below target |
| [memo_found](main.bend#L260) | 65% | 85% | 2.00 | 22% | below target |
| [memo_read](main.bend#L267) | 70% | 79% | 1.99 | 24% | below target |
| [Memo.apply](main.bend#L271) | 62% | 84% | 2.33 | 44% | uncertain |
| [Memo.begin](main.bend#L276) | 88% | 71% | 1.85 | 23% | below target |
| [Memo.succeed](main.bend#L279) | 88% | 67% | 1.70 | 17% | below target |
| [Memo.fail](main.bend#L282) | 91% | 74% | 1.62 | 14% | below target |
| [Memo.cancel](main.bend#L285) | 91% | 80% | 1.81 | 19% | below target |

## Disposition

**Style attention remains open.** `Memo.apply` has the strongest memetic mean
(2.33/4), but its 44% target mass is uncertain. Its full level distribution is
`[0%, 13%, 43%, 41%, 3%]`; ranking first is not a pass.

The previously quoted `memo_commit` earns 85% conceptual and 83% delight target
mass, but only 7% memetic mass (1.67/4). The explicit rejection-versus-write
branches support the earlier structural observation; they do not support a claim
that the pattern has the desired distinctive pull. No such pass is claimed.

One concrete future reading hypothesis is the `Cell.step` transition grammar:
its Pending branch repeats the same rejection in three action cases, while
Evaluating exposes four different transitions. A representation that makes
legal edges and the shared rejection rule visible might improve conceptual
compression without hiding returned ownership. This is an untested opportunity,
not an approved rewrite or a predicted score increase.

Tiny constructors such as `Scopes.new` and `Scopes.from` receive 0% memetic
mass despite directly expressing their initialization contract. Adding layers
or decorative names would not add an idea. Their below-target results remain
visible; no automatic pass or human-agreement claim overrides them.

This request adds reporting and verified receipt reuse only. It does not start
an implementation batch or alter the coordinator-owned campaign queue. The
prior no-alternative rationale is historical: the current style workflow
explicitly rates a single existing implementation. No code or rubric changed,
and semantic gates were not rerun for this reporting-only increment.
