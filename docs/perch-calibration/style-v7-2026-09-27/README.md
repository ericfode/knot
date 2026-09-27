# Version 7 figure reviews

Rubric version 7 judges identity at the figure against the pattern sheet
[KNOT-SHAPES.md](../../KNOT-SHAPES.md). This record holds the pre-registered
expectations for its first live use and, once run, the receipts beside them.

## Status

Live review: **completed 2026-09-27**, one run per figure, jev-1.13.0, 66 provider
requests in total, sheet and manifests unchanged from the frozen expectations,
source fresh throughout. Receipts are the four compressed `*.json.gz` files;
[results.json](results.json) is a derived summary. Nothing was rerun and no
threshold, sheet text or manifest was edited after seeing a result.

```sh
npm run lint:style -- --live --figure=docs/style-campaign/figures/<id>.json --jobs=8 \
  --output=docs/perch-calibration/style-v7-2026-09-27/<id>.json.gz
```

Probabilities are mass at the required level: level 3 for leads and
compositions, level 2 for supporting members.

| Figure | Meets all required | Composition memetic / anticipation / payoff | Declared lead memetic / anticipation / payoff |
| --- | ---: | --- | --- |
| owned-time-slicing (21) | 9 | .26 below / .33 below / .47 uncertain | `run` .37 below / .82 meets / .69 meets |
| int-map-paths (23) | 20 | .22 below / .44 uncertain / .72 meets | `edit_path` .70 / .63 / .61, all meet |
| symbols-trie (8) | 5 | .23 / .27 / .31, all below | `Trie.get` .48 uncertain / .59 uncertain / .74 meets; `Trie.insert` .29 below / .47 uncertain / .76 meets |
| compiler-pipeline (6) | 1 | .12 / .08 / .20, all below | `source` .19 below / .16 below / .51 uncertain |

No figure qualifies. Compression and Delight meet on every declaration in every
figure except three uncertain Delight results. Proof fills were advisory in the
two figures that have them: 7 of 20 ratings meet in owned-time-slicing, 14 of
25 in int-map-paths.

## Expectations against results

| Expectation | Result |
| --- | --- |
| IntMap lead `edit_path` at least .30 on each axis, meets or uncertain on one | Exceeded: .70 / .63 / .61 all meet, from .09 / .08 / .03 under version 5 |
| IntMap composition anticipation above .30 | Met: .44, from .04 |
| IntMap composition memetic meets or uncertain | Missed: .22, from .30 |
| Owned-time-slicing lead `run` memetic meets or uncertain | Missed: .37 below; anticipation and payoff rated and meet |
| Owned-time-slicing composition anticipation clearly above .04 to .06 | Met: .33, still below target |
| Symbols leads both meet memetic 3 | Missed: `Trie.get` .48 uncertain, `Trie.insert` .29 below |
| Symbols datatypes rated with complete context | Met: no unavailable diagnostics anywhere |
| Compiler pipeline composition available and below target | Met: .12 / .08 / .20 |

## Findings

- **The figure context moved Payoff and Anticipation where laws and mirrored
  proofs are in the group.** IntMap composition payoff went from .11 to .72 and
  meets; anticipation from .04 to .44. Owned-time-slicing anticipation went
  from the .04 to .06 seen in every version 5 composition to .33.
- **Memetic identity at level 3 stays below target for every composition**
  (.12 to .26) and for three of five declared leads. The sheet makes shapes
  recognizable at level 2, which supporting members now pass broadly, but it
  does not by itself create the pull that level 3 asks for.
- **The model classifies the figure's datatype as leading** in three of four
  figures (`Run`, `Task`, `Frame`, `IntMap`, `Trie`), which the role rubric's
  own wording, the organizing representation, invites. Those datatypes then fail
  level 3 memetic identity. The sheet lists datatype shapes S2 and S3 as
  instantiable forms. Whether a datatype inside a figure should carry the lead
  bar is an unresolved policy question, recorded here, not tuned away.
- **Uncertain roles fall to level 3 by design** (`combine`, `step_parts`,
  `step`, `one_tick`, `Limits`, `parsed`) and fail. A manifest can only raise
  a declaration; letting owners declare supporting members would need its own
  bypass controls before adoption.
- **Symbols moved the wrong way** relative to the version 3 record (`Trie.get`
  .62 to .48, `Trie.insert` .54 to .29). The rubric, the sheet and the
  appeal-independence wording all differ, so this is a direction, not a
  measured regression of the same instrument.
- **Live evidence remains model judgment.** No human preference has been
  recorded for figures. The user's five taste anchors are still required
  before any threshold discussion.

## Human anchors

The user records taste anchors in a private page,
<https://claude.ai/artifact/PFwdEppca7TSeUCpPCx1YY>. Answers live in that
artifact's database (collections `anchors`, `notes`, `custom`) and are read
back with the Artifact data tool, never retyped.

First reading, 2026-09-27, exported to [human-anchors.json](human-anchors.json):
18 of 28 sampled declarations tagged **fine but generic**, none want-more, none
over-styled, no reasons. In chat: none of it was remotely too much, the edge is
much further out, and all of it was a little boring to read. Two consequences:

- The negative controls assumed so far (decoration, symbols, renaming, extra
  layers) sit far inside the user's tolerance. "Over-styled" has no instance in
  the corpus and must be constructed.
- The model's Delight passes (level 3 on nearly every declaration in every
  figure) disagree with the user's reading. The memetic axis failing broadly
  agrees with it.

[The ladder](../../style-campaign/ladder/README.md) supplies five compiled
treatments of the time-slicing figure, each further out, for the user to tag.
Model review of the rungs waits until those verdicts are recorded.

## Pre-registered expectations

[expectations.json](expectations.json) records, before any provider response,
what the author expects for each lead, composition and member set, with the v5
or v3 prior it should be compared against. The hashes of the rubric, the sheet
and the four manifests are frozen there. A result that misses an expectation is
a calibration finding for the review log; it is not a reason to edit the sheet,
a manifest or a threshold.

## Offline verification

`npm run lint:verify` passes 93 of 94 tests plus law-rule wiring with no
provider contact. The one failure is inherited from main: the parser-coverage
test rejects `packages/int_map/locality/PROOF.bend` (`Expected a term; observed
'~'`), the observer gap for imported template-law fills that the review log
already records. Parser, observer, vendor and test files are identical to main;
the IntMap owner's source is untouched here. `tests/perch-style-figure.test.mjs` covers the sheet's presence in
every request and its part in each identity, manifest validation, declared-lead
monotonicity, advisory proof fills inside figures, opaque interface resolution,
stale sheet disclosure, figure-as-context for members and inventory scopes.
All four real manifests validate with zero truncated member contexts and zero
unresolved references; the compiler pipeline composition was unavailable under
version 5.

## Limits

No human preference has been recorded under any rubric version. A model
distribution is a reading prediction, not agreement with the user. Version 7 is
a change to the unit and context of judgment; its thresholds are the version 5
and 6 thresholds, and it keeps version 6's independence of memetic appeal from
conceptual value. Historical receipts keep their rubric identity and cannot be reused
under the new hash.

## The ladder: judge against user on the same six files

The user ranked seven treatments of the time-slicing machine before any model
review: current code < B < C < F, with D and E over-styled because one-letter
names are too hard to read and A "boring"; nothing was flagged too much among
the kept rungs, and the stated wish is F's algebra with B's human vocabulary
([ladder](../../style-campaign/ladder/README.md), [human-anchors.json](human-anchors.json)).
Expectations were frozen in [ladder-expectations.json](ladder-expectations.json),
then each rung was reviewed once as its own figure with the shared task,
jev-1.13.0, sheet and rubric unchanged
([ladder-results.json](ladder-results.json), receipts `ladder-*.json.gz`).

| Rung | User | Lead memetic / anticipation / payoff | Composition memetic / anticipation / payoff | Mean Delight mass | Mean memetic mass |
| --- | --- | --- | --- | ---: | ---: |
| A | boring | `run` .25 / .63 / .42 | .12 / .22 / .26 | .78 | .35 |
| B | good, dull; beats current | `give` .18 / .36 / .35 | .21 / .27 / .22 | .63 | .39 |
| C | good, dull; beats B | `give` .17 / .39 / .35 | .19 / .24 / .23 | .63 | .43 |
| D | over-styled | `give` .47 / .40 / .32 | .33 / .28 / .20 | .60 | .55 |
| E | over-styled | `g` .16 / .22 / .24 | .14 / .19 / .15 | .49 | .29 |
| F | beats C and B | `give` .15 / .35 / .32 | .26 / .36 / .32 | .65 | .43 |

Findings, in order of weight:

- **Delight is inverted against the user on this ladder.** The judge's Delight
  is highest on A, the rung the user calls boring, and falls as ideas are added
  through B, C and F. The user's fun order runs the other way. This is the axis
  that passed nearly every declaration in every figure review; it should now be
  read as a measure of conventional smoothness, not of the user's pleasure.
- **Memetic identity rewards the rung the user rejects.** D has the highest
  lead memetic mass (.47), the highest composition memetic mass (.33) and the
  highest mean (.55). The user's edge is exactly D's abbreviation. The rubric's
  welcome for terse learned vocabulary, kept through versions 6 and 7, points
  the wrong way for this reader.
- **Compression, and composition anticipation and payoff, agree on F.** F is
  the only rung where every definition meets compression, and its composition
  anticipation (.36) and payoff (.32) are the highest. These are the axes that
  track "an idea was added". They do not separate B from C from A, which the
  user does.
- **E is marked down by the judge as well** (Delight 2 meet, 7 uncertain, 2
  below), so the judge finds the far edge, just one rung too late.

Consequence for the framework: the human anchors now exist, and the two axes
that were passing most broadly are the two that disagree with them. No wording
or threshold changes here; the ladder is now a development set. A second ladder
on a different figure, ranked by the user before review, is the held-out set
any version 8 wording must be tested against.
