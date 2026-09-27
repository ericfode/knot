# Rubric v8: calibrated to the user's blind taste anchors

**Request (2026-09-27).** "Update the perch rules so that jev picks the same stuff."

**Human anchors.** Two blind rounds on 34 behavior-identical renderings of four
tasks ([taste duel](../taste-duel-2026-09-27/README.md)). There are 4 lineups
and 21 duels, which give 59 human preference pairs.

**Judge.** jev-1.13.0 through the production style path. Each rendering is run
by `runStyleRanking --live` in its own scratch workspace, with its task
contract, so every run includes declarations, the task-potential judgment and
the whole-file composition. Total spend was 1,223 provider requests. Nothing
was rerolled.

## Method

1. **Baseline.** The v6 rubric was run on all 34 renderings (364 requests).
   Repeating the 9 bitpath renderings (117 requests) moved the overall score by
   at most 0.007, so pairs within 0.01 are treated as ties.
2. **Split by task.** Development is bitpath and fuel. Held out are pipeline
   and slots. The drafters saw only the development answers, renderings and v6
   scores ([dev-brief](dev-brief/)). Before any candidate was scored, the
   [pre-registration](preregistration.md) fixed three things:
   - the metric: `overall`, the mean of declaration compression, declaration
     delight, and composition memetic, anticipation and payoff;
   - the tie rule and the selection rule;
   - the held-out acceptance thresholds.
3. **Three candidates.** Three strategies were drafted and each was critiqued
   for leakage, generality and lowered bars ([candidates](candidates/)):
   - `register`: the preferred register stated positively, with absolute caps
     on the failure families;
   - `minimal`: the smallest edit to v6;
   - `contract`: anticipation and payoff built on the stated contract, and
     memetic as the imitable shape.
4. **Selection on development tasks (189 requests each).** `register`
   and `contract` tied at 12/12 duels and 32.5/34 pairs. The pre-registered tie
   break, the smaller rubric, selected `contract` (1.42× v6 text, against
   1.46×).
5. **Held-out check, run once (175 requests).** `contract` on pipeline and
   slots.

## Results

| Rubric | Dev duels | Dev pairs | Held-out duels | Held-out pairs | All duels | All pairs |
|---|---|---|---|---|---|---|
| v6 | 5.5/12 | 51% | 3.5/9 | 52% | 9/21 | 52% |
| minimal | 11/12 | 90% | — | — | — | — |
| register | 12/12 | 96% | — | — | — | — |
| **contract → v8** | **12/12** | **96%** | **7.5/9** | **84%** | **19.5/21** | **91%** |

v8 met all three pre-registered thresholds:

| Threshold | Required | Result |
|---|---|---|
| Held-out duels | ≥ 7/9 | 7.5/9 |
| Held-out pairs | ≥ 76% | 84% |
| Dev duels | ≥ 10/12 | 12/12 |

Per axis, over all 59 pairs, v8 moved agreement as follows (v6 → v8):

| Axis | v6 | v8 |
|---|---|---|
| Composition memetic | 40% | 70% |
| Composition anticipation | 51% | 86% |
| Composition payoff | 61% | 75% |
| Declaration delight | 63% | 83% |
| Declaration compression | 63% | 70% |

On the held-out tasks alone (25 pairs), v8's per-axis agreement is weakest on
the axes this work cares most about:

| Axis | Held-out agreement |
|---|---|
| Composition memetic | 62% |
| Composition anticipation | 80% |
| Composition payoff | 68% |
| Declaration delight | 90% |
| Declaration compression | 72% |
| Declaration memetic | 76% |

The overall mean agrees more than composition memetic does alone, so memetic
is the least-validated axis.

**Ordering is not pass or fail.** Under v8 no rendering is fully qualified,
including the user's favourites.

- **Composition passes for the favourites.** It meets its targets for bitpath,
  fuel and slots algebra and for pipeline literate without its puzzle. Mythic,
  baroque and golf mostly fall below target, and literate is below or
  uncertain.
- **Leading declarations fail the favourites.** Small core definitions (for
  example fuel's owe/tick/run) still miss per-declaration Anticipation and
  Payoff at level 3 at 60%.
- **pipeline algebra's composition is still below target.**

So v8 agrees with the user on ranking and largely on composition pass or fail,
but not on declaration qualification. Whether leading declarations should keep
the level-3 Anticipation and Payoff bar is a threshold decision for the user.

**Cheapest lever: a law comment.** On the bitpath development task, adding the
law header alone moved composition M/A/P from 0.88/0.73/0.44 to
1.00/0.99/0.84. The user does prefer stated laws, but nothing deterministic
checks a comment's claim. A code-improvement brief should therefore ask for
real `law` declarations with proofs, which the pinned compiler checks, not
unchecked law comments.

Absolute behaviour on the development tasks. The algebra renderings the user
preferred now meet the whole-mechanism targets: bitpath M/A/P at level 3 or
above scores 1.00/0.99/0.84, and fuel scores 0.97/0.96/0.83. The rejected
ornamental, mythic, golf and literate renderings fall below them. Under v6 it
was the other way round: mythic and baroque reached 0.93 to 0.98 on memetic.

Remaining misses (held-out):

- **d8, slots.** The user preferred the baroque rendering over the literate
  one; v8 prefers literate by 0.25. This is the round's one surprising human
  preference.
- **e11, pipeline.** Prose volume. The difference is −0.003, inside the tie
  band.

## What changed (v6 → v8)

Only these fields changed:

- dimension and diagnostic instructions and level texts;
- `style_role.composition_instructions`;
- the new `style_role.composition_axis_instructions`.

Targets, thresholds, probabilities, level counts, roles, criticality and
potential are byte-identical.

- **Memetic identity** is the imitable shape of the mechanism: a
  representation, a small family of primitives with stated laws, an aligned
  case table, a law checked by its proof, or a recurrence a fluent reader would
  copy into new code. Costume, ornament, narration, puzzles and crushed
  abbreviation earn nothing and lower the score when they hide the shape.
  Costume here means a sustained borrowed world of names that must be
  translated back.
- **Anticipation** comes from the stated contract: types, operation names and
  compact laws, strongest when the laws let the reader predict the
  definitions. Suspense devices score below a plain up-front statement.
- **Payoff** is the definitions visibly realizing the contract. A law checked
  by its proof resolves most, then a law that holds by construction. Prose
  answers and reveals resolve nothing.
- **Delight** is penalized by three opposite excesses: prose volume, long
  restating names and crushed cryptic density.
- **Compression** is conceptual, not typographic. Costume and pass-through
  layers add concepts without explaining any.

## Limits

- **One person, two short rounds.** All answers were given at full strength.
  These are anchors, not a population model.
- **Familiarity.** In round 2 the algebra bases had already been seen and
  chosen, which may favour them. Both literate duels went against the base,
  which argues against a pure familiarity effect.
- **Author knowledge.** The coordinator knew every answer. Held out means that
  the drafters never saw the held-out tasks, and that no candidate was revised
  after its held-out score. Both principles the rubric names were learned on
  the development tasks: costume (from the mythic renaming) and suspense (from
  the riddle). Held-out duels test them on new tasks, on new factors
  (notation, removing the puzzle, prose volume), and on style pairs the
  drafters never saw.
- **Seen controls.** All 34 renderings have now been shown to the judge and
  are no longer held-out. A future rubric change needs fresh controls.
- **Real Knot code is unmeasured.** v8 has not been run on real repository
  code here. Its effect on the inventory, and on the 0/27 historical
  compositions, is unmeasured.
- **Superseded definition.** v8 replaces v6's memetic definition, at the
  user's request. Earlier receipts keep their rubric identity and are not
  reused.
- **Conflicting branch.** An unmerged branch (`claude/interesting-lamport-c393ad`)
  carries a different rubric labelled version 7, and it would need to be
  reconciled against these anchors.

## Reproduce

```sh
node run.mjs RUBRIC.json OUT_DIR bitpath,fuel,pipeline,slots   # paid; reads the main checkout's .env
python3 analyze.py OUT_DIR --json OUT.json                       # offline
```

`runs/*.json.gz` hold every report, and `runs/*-agreement.*` hold each
analysis.
