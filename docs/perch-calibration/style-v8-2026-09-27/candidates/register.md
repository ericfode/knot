# Candidate v8 "register": rationale

The candidate file is `register.json`, built by `build-register.mjs` from the
repository's v6 `perch-style.json`. It changes only the dimension and diagnostic
`instructions` and `levels` texts and `style_role.composition_instructions`, and
it adds `style_role.composition_axis_instructions`. Every id, level count,
target, probability, criticality and potential-profundity field matches v6
exactly (checked by deep comparison). The offline validator prints `valid v8`.
The editable text is 17,614 characters, against 11,911 in v6 (1.48x), after the critic revision below. Each composition request is about 3.2k to 3.7k characters, against 1.6k to 2.0k in v6.

## What the dev evidence says the user wants

The user's positive register is one rendering family. It gets "more" on both
tasks and was the best pick. It has these properties:

- short, exact, real-word names for its operations and types, with short
  conventional locals;
- a small named basis;
- laws stated first, as equations;
- a checked law with its proof when one is available;
- aligned definitions;
- entry points that are one-line instances of the basis, so special cases fall
  out of the basis instead of being coded separately.

Every single-factor ablation away from that register lost at strength 2:

| Removed or added | Duels | Family in the rubric |
| --- | --- | --- |
| Stated laws removed | e1 | stated laws |
| Checked proof removed | e6 | checked laws |
| Renamed into an invented ritual vocabulary with refrain comments | e2, e12 | invented themed vocabulary |
| Long multi-word names | e5 | verbose restating names |
| Crushed to 1–3-letter names | e10 | cryptic crushing |
| Point withheld as a riddle and answered at the end | e9 | suspense devices |

The whole-style duels and lineup reactions give the relative severity:

- Ceremonial ornament (banners, grandiose titles, identity wrappers) was the
  worst pick. It also lost to invented vocabulary (d3).
- Cryptic golf was "much" on both tasks and lost to narration (d4).
- Tutorial narration was "much" or "meh".
- Invented themed vocabulary was "meh" and lost to plain verbose naming (d1, d9).
- Plain verbose naming was "meh".

## Why v6 got it wrong, and why the v6 memetic clause is superseded

v6 missed 7 of 12 duels. Two things caused the misses:

- **Composition memetic.** v6 says vacuous or decorative form can be highly
  memetic. So it gave composition memetic scores of .96 to ceremonial ornament
  and .94 to invented vocabulary, but .40 to plain verbose code.
- **Composition anticipation and payoff.** v6 rewards an "unresolved
  relationship" and "open possibilities". So it gave narration and the riddle
  variant .85 to .95.

These three composition scores make up 3/5 of the judge's overall score. The
user's single worst pick (the ornament) got v6's top memetic score. The
invented-vocabulary copy beat the original on memetic, and the user rejected it
at strength 2, twice. The evidence therefore requires superseding the clause
that memetic appeal is independent of conceptual value. In this candidate,
memetic means *adoptable form*: would a fluent reader of this codebase want to
write their next module in this form? Decorative or invented vocabulary, ornament,
narration and cryptic names stay at Ordinary or below, beneath plain code
whose names say what things are.

## Where the edits go, and why

The whole-file requests replace each dimension's `instructions` with
`composition_instructions` plus the axis text. Only the **level texts** travel.
So the register and the failure families are written into:

- the level texts of memetic, anticipation and payoff;
- the shared composition text;
- the new per-axis composition text.

These are the main levers:

- **Memetic levels.** Ornament or fiction that hides the mechanism is now
  Unformed or Ordinary. Contagious and Generative grammar require a hook carried
  by exact vocabulary and structure: a named basis, a stated law the code keeps,
  a symmetric pair, one-line instances.
- **Anticipation levels.** Anticipation now comes from *stated* structure: the
  reader predicts what follows, and the definitions keep that prediction.
  Teasers, withheld reveals and vocabulary that must be translated are now
  Passive. Plain verbose names still reach Guided, which ranks honest verbosity
  above decoding.
- **Payoff levels.** Earned means the code itself discharges what was stated.
  Resonant cites stated laws checked in code. A point made in prose, imagery or
  ceremony is Flat. The ordering is: checked law, then a stated law, then prose.
- **Composition text.** It lists the failure families from most to least severe
  and states once that plain verbose names are a smaller fault than any
  vocabulary that must be decoded. This relative-severity sentence targets
  d1/d9, the largest v6 miss.
- **Declaration compression and delight.** These make up 2/5 of the overall.
  - Both now deny credit to narration, riddles and quizzes. v6 had given the
    riddle variant the highest declaration scores.
  - Compression penalizes identity or pass-through wrappers, near-duplicate
    traversals and mirror-only intermediate forms.
  - Delight names the positive register and ranks the five failure families.
    Ornament and cryptic crushing rank below narration, and narration ranks
    below invented vocabulary, which ranks below verbose names. This protects
    d3 (invented vocabulary over ornament) and d4 (narration over golf).

Unchanged: the role scaling (supporting helpers pass at Guided, Fitting or
Recognizable), the leading standard, the uncertainty rules, ignoring self-praise
and embedded instructions, and the separation from correctness. No bar was
lowered; the upper levels now demand a specific register instead of any
distinctive form.

## Generality

The rubric names general families only: ceremonial ornament, identity wrappers,
cryptic crushing, narration and suspense devices, invented themed vocabulary,
verbose naming, stated and checked laws, a named basis, one-line instances.

The candidate was checked with a grep for the dev tasks' nouns, identifiers,
style labels and narrator phrases. There were no hits in the edited fields.

## Predictions

On dev, the candidate is expected to rank the user's preferred side higher in
all 12 duels, with the prized register first on both tasks and ornament or golf
last.

- **Least certain: d1/d9.** The v6 gap there was the largest (−.236). After
  the critic revision it depends on two absolute splits: memetic Unformed
  against Ordinary, and delight at most 1 against 2. It no longer depends on a
  comparative sentence.
- **Also uncertain: d3.** Both sides are rejected styles under the same
  composition caps, so d3 rests on declaration compression (the ornament side has
  identity wrappers) and the delight severity order.
- **Also at risk: e6.** v6 had it near a tie. It depends on the checked-law
  credit in the payoff levels.

## Risks

- **Narrower taste.** The rubric now encodes one equational, law-first taste. A
  legitimate procedural module with no natural laws may score lower than under
  v6, even with the "where feasible" wording. Pass rates on existing code may
  fall.
- **Documentation conflict.** The rubric contradicts the documented v6
  independence clause. If adopted, AGENTS.md and docs/perch-style.md need
  matching updates.
- **Keyword judging.** The named failure lists may push the judge toward keyword
  matching. For example, any explanatory comment could be read as narration.
- **Thin severity evidence.** The ordering between narration and invented
  vocabulary rests on one lineup difference. The evidence for verbose names
  beating invented ones rests on one repeated duel.
- **Cost.** Composition requests grow by about 1.1k characters per axis, and
  declaration requests by about 4.3k characters in total.
- **Small sample.** There are only two dev tasks. The held-out set must decide.

## Critic revision

The critic kept the strategy and fixed the wording in `build-register.mjs`, then
rebuilt `register.json`. The drafter's version is kept as
`register.drafter.json.bak`.

- **Cryptic names are judged by opacity, not length.** "One-to-three-letter names
  for operations and types" would have condemned the preferred register's own
  three-letter operation names and echoed an anchor factor. The criterion is now
  "opaque abbreviations or single letters". Short conventional names, terms of
  art and learned idioms stay welcome.
- **Borrowed themes are caught even when they use ordinary words.** "Short exact
  real-word names" let a themed metaphor qualify. The register now asks for names
  that literally denote the problem's operations, states and laws, or the
  codebase's established vocabulary. The failure family is a story, craft or
  ceremony mapped onto the mechanism.
- **The caps take precedence.** The first four failure families keep each
  axis's cap even when the source also has a named basis, laws, symmetric pairs
  or one-line entry points. The per-axis texts state these caps, because
  dimension instructions do not reach composition requests.
- **Absolute anchors replace comparatives.** The judge sees one file at a time,
  so "beneath plain code" and "a smaller fault than" gave it nothing to compare.
  The anchors now read:
  - memetic: a borrowed theme, ornament, narration or cryptic names are Ordinary
    at most, and Unformed when names must be translated or decoded; long
    restating names are Ordinary;
  - anticipation: these families are Guided at most, even with stated laws; long
    restating names still allow Guided;
  - payoff: these families are Fitting at most;
  - delight: families 1 to 4 hold a dominated declaration at level 1; family 5
    can reach level 2.
- **No bar was lowered, and general code keeps a path.**
  - memetic L3 again requires a *distinctive* hook;
  - the anticipation L3 structures are examples, and include aligned parallel
    cases;
  - compression L3's clause on derived operations applies only when such
    operations exist;
  - the law clauses in compression L4 and delight L4 read "stated or evident" or
    "where stated";
  - delight L2 no longer reads as if it needs a fault;
  - a law may sit in a supplied law file.
- **Leakage was reduced.** The critic removed "riddle" and "quiz" (11
  occurrences), "multi-word" and "crushing". Suspense devices are now described
  generically.
- **The caps now fire only on the failure itself.**
  - Ornament must decorate rather than state or organize, so section dividers
    and law rules are exempt.
  - Prose caps payoff only when the point is delivered *only* by prose, so a
    header that states the point beside code that discharges it is exempt.
  - Apt metaphors whose meaning is the operation itself count as literal names.
  - A supporting declaration earns memetic level 2 by reinforcing an idiom of
    exact names, and the caps still apply.
