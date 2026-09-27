# Candidate v8 "minimal": rationale

The candidate file is `minimal.json`. It is built reproducibly by `build-minimal.cjs`, which makes exact
substring replacements on v6 and fails if an anchor is missing. The build validates as `valid v8`. After the
permitted fields are removed, it deep-equals v6, with key order preserved. Editable text grew from 11,911 to
14,803 characters (1.24x) after the critic revision below. Per composition request, the text grows by about 750 to 840 characters.

## Where the lever is

Dev `overall` is the mean of five parts:

- declaration brain and delight: 40%
- composition memetic, anticipation and payoff: 60%

A composition request contains only these texts:

1. `composition_instructions`
2. `composition_axis_instructions[axis]`
3. the "Apply the … levels" line
4. the axis **levels**

It does not include the dimension's own `instructions`. The composition fixes therefore sit in those four places. The declaration-level
memetic, anticipation and payoff instruction edits only keep the declaration gates consistent.

## Dev misses and their drivers (v6 algebra minus rival)

| miss | driver | edit family |
| --- | --- | --- |
| e9 algebra > riddle (-0.127) | composition anticipation -0.29, composition payoff -0.20; riddle declaration brain and delight also higher | suspense is not preparation, and a reveal is not payoff |
| e2/e12 algebra > mythic rename (-0.047) | composition memetic -0.17, composition anticipation -0.09 | costume is not a hook, and it adds friction on every axis |
| d2 algebra > baroque (-0.019) | composition memetic -0.20; baroque declaration delight 0.68 | costume, plus penalties for ornament and identity wrappers |
| e6 proof > no proof (+0.003, a tie) | only payoff favors the proof (+0.035) | a checked law outranks an asserted one |
| d1/d9 deadpan > mythic (-0.236) | all three composition axes (memetic +0.53, anticipation +0.31, payoff +0.27 for mythic) | costume friction (expected to narrow the gap, perhaps not flip it) |

Evidence for dropping the v6 rule that memetic value is independent of conceptual value: the user's lineup scale
is literally "want more of this" versus "no pull". The user gave *no pull* to the mythic renderings, *repels* to
baroque and *want more* to algebra, and preferred algebra ±2 in every costume and riddle ablation of identical code.
The user's felt pull therefore comes from the mechanism's own stated relationships, not from a theme laid over it.

## Edits

> **Superseded wording.** Items 1 to 10 below record the drafter's edits and their dev-evidence targets. For the exact current strings, see the "Critic revision" section at the end and `minimal.json`. That revision replaces the style-label words with categories and turns suspense and staged reveals into penalties rather than zero credit. It restates proof credit as an ordering instead of a level exemplar, so payoff L3 no longer names a proof. It also changes "Theme vocabulary" to "Invented theme vocabulary" in memetic L2 and adds the honest-name guard. Where an item below quotes a phrase that differs from `minimal.json`, the JSON is authoritative.

1. **`composition_instructions`** (d1, d2, d9, e2, e12). I replaced "vacuity, decorative form … does not disqualify"
   and "do not import … other axes". The new text puts the hook in the code's notation, names, symmetry and stated
   relationships. It calls a theme laid over ordinary code costume, and it counts translating that costume back as
   friction on every composition axis.
2. **`composition_axis_instructions.highly_memetic`** (d2, e2, e12; protects d4 and e10). The strongest hook is a true,
   quotable relationship, such as a stated law, a one-line reduction or a small exact vocabulary. Costume, ornament,
   staged puzzles and crushed cryptic code earn nothing.
3. **`composition_axis_instructions.anticipation`** (e9; protects e1). Stating the representation and its laws up
   front is the strongest setup. Withheld answers, riddles, quizzes, teasers and promises to explain later earn no credit.
4. **`composition_axis_instructions.payoff`** (e6, e9; protects e1). The ranking runs in three steps: no law, then a
   stated law that the definitions visibly discharge, then that law with a checked in-code proof. A riddle or quiz answered in comments, or a closing
   refrain, is narrative resolution and earns no credit.
5. **Memetic levels 2, 3 and 4** (shared by the declaration and composition requests; d2, e2, e12). I removed "vacuous,
   nonsensical, useless or incorrect" and "need not explain a mechanism". Level 3's hook now lives in the code's
   notation, names or stated relationships. Level 4's grammar is the mechanism's own. Theme vocabulary alone does not reach level 2.
6. **Anticipation level 3** (e9). "open possibilities invite engagement" rewarded suspense. It now reads "stated
   structure makes its possibilities visible … Withheld answers do not qualify."
7. **Payoff level 3** (e6, e9). The completion must happen *in the code*, for example definitions or a checked proof
   that discharge a stated law. A reveal staged in comments does not qualify.
8. **Brain instructions** (e6, e9, d2). Stated laws count when the code discharges them. A checked proof that
   follows the definitions' recursion is evidence that invariants arise from structure. Theme renaming, identity
   wrappers, ceremonial layers and puzzle framing add no compression.
9. **Delight instructions** (d2, d1, d9, e2, e9; protects d4 and e10). "Terse names" became "short exact words";
   cryptic abbreviations and crushed layout force decoding. Identity wrappers and ornament join the penalty list.
   Theme vocabulary that must be translated back, and suspense devices, count as friction.
10. **Memetic, anticipation and payoff declaration `instructions`** (consistency only). These replace the matching
    independence and "unresolved relationship" wording, so the declaration gates agree with the composition text.
    "renaming" is removed from the memetic list of what "can contribute", because it contradicted the costume clause.

## Kept on purpose

- **Stated laws in comments remain creditable** as preparation (e1).
- **Plain or explicit names are not rewarded** (e5), because rewarding them would also lift long names.
- **Nothing rewards terseness further** (e10).
- **The penalty is aimed at theme plus ornament and indirection**, not at theme alone. This leaves fuel mythic above
  baroque (d3) through brain and delight.

## Risks

- d1/d9 need mythic to fall below deadpan on all three composition axes. Minimal wording may only narrow a gap of 0.236.
- The suspense clause lowers fuel literate (v6 composition anticipation 0.945, payoff 0.83). d4 (literate > golf)
  now relies on golf staying low. The cryptic-abbreviation clause is there to protect that margin.
- The candidate reverses the 2026-09-27 v6 independence clause in AGENTS.md and docs/perch-style.md. Adopting it
  would require updating those documents, which this candidate does not do.
- The judge may read up-front law comments as "self-praise", or read any closing summary comment as a "staged reveal".
- There are only two tasks and 12 duels. The held-out validation decides whether the edits generalize.

## Critic revision (applied in `build-minimal.cjs`, rebuilt, still `valid v8`, rest deep-equal to v6)

1. **Generality.** Style labels and factor words ("mythic", "ritual", "chant", "riddle", "quiz", "hint trail",
   "promise") are replaced with categories: invented ceremonial or story-world vocabulary, comment refrains,
   a question posed early and answered later, planted hints, teasers, reveals deferred to the end.
2. **Honest figurative names.** One clause in the memetic instructions and composition instructions says that an
   established or self-explaining figurative name is vocabulary, not costume. Costume means a sustained invented
   world that the reader must map back onto the mechanism. This keeps metaphorical but exact names in ordinary Knot code out of the penalty.
3. **Suspense is a penalty, not zero credit.** The riddle ablation states the same laws as the preferred code, and it
   led on declaration brain (+0.060) and delight (+0.028). If suspense only earned zero credit, the composition
   axes would at best tie, and the riddle would still win e9 by about 0.018. The anticipation instructions,
   anticipation axis text, payoff instructions and payoff axis text now treat withheld answers and staged reveals as
   delayed clarification or artificial buildup that lowers the score. This reuses v6's own "delayed clarification" and
   "artificial buildup" penalties.
4. **No bar-lowering for proof-heavy code.** Proof credit is now stated as an ordering (checked proof > asserted law >
   no law) in the brain and payoff instructions. It no longer appears as an exemplar inside brain L4 wording or payoff L3.
   Payoff L3 keeps only "in the code" and the exclusion of reveals staged in comments.
5. **Anticipation wording.** L3 now says visible structure (types, names, parallel forms or stated laws), so code
   without comments can still reach Inviting. The leading cue "a stated relationship still to be realized" read as a
   tease. It is now "a stated law or relationship that the following definitions carry out".
6. **Independence clause narrowed to the evidence.** "true" became "actual" or "real". The dev evidence concerns
   costume and suspense, not correctness. No permissive "need not be useful" sentence was restored next to the costume clause.
7. **No new lever aimed at narrated or tutorial styles.** Literate enters the primary metric only in d4, where the
   user prefers it.

Added risks:

- **Honest-name loophole.** A judge could call a theme that sits next to the domain "self-explaining", for example fire names on fuel-like code. The definition "sustained invented world" is what has to catch such a theme.
- **Legitimate Q&A comments.** Ordinary question-and-answer comments ("why does this terminate? because ...") now draw an anticipation penalty.
- **Doc drift.** "Terse names" became "Short exact words", and the independence clause is reversed for costume and suspense. Both change the rubric's meaning relative to AGENTS.md and docs/perch-style.md, so adopting the rubric means updating those documents.
- **Weaker e9 flip.** Brain gives riddle framing only "no compression", so the riddle's declaration lead of about 0.018 remains. e9 flips only if the composition penalties plus delight friction outweigh that lead.
