# Candidate v8 "contract": rationale

File: `contract.json` (built by `build-contract.cjs` from the repository `perch-style.json`, then revised in place by `critic-contract.cjs`; the drafter's version is kept as `contract.drafter.json.bak`).
Validation: `assessStyle([], c)` prints `valid v8`. A deep comparison with v6 shows that only
the allowed paths change: `version`, dimension and diagnostic `instructions`/`levels` texts,
`style_role.composition_instructions`, and the new `style_role.composition_axis_instructions`.
Level counts, ids, targets, probabilities, criticality and potential profundity are byte-identical.
After the critic pass, the editable text is 17,114 characters against 11,911 in v6 (1.44x). Across all
instruction and level text it is 1.30x. Per request, the ratio is 1.25x for declarations and 1.58x for compositions. A textual diff against v6 confirms that only
the edited strings, `version` and the new key changed.

## What the dev evidence says

- The user's top pick is compact code that states its laws. Its names are short and exact,
  its case tables are aligned, and where possible a checked proof sits beside the code.
  Every single-factor ablation of it loses at strength 2. The ablations removed the laws,
  removed the proof, lengthened the names, crushed the layout, renamed everything into a
  ritual vocabulary, or reframed the comments as a puzzle.
- The user reacts to three different excesses as "too much": ornamental ceremony built from
  pass-through layers, crushed cryptic density, and heavy tutorial narration. Plain, verbose
  code and costume-vocabulary code only get "meh". In a direct duel, plain verbose code
  beats costume code.
- The v6 misses come mainly from the three composition axes, which make up 3/5 of the
  overall score:
  - Costume and ornament score about 0.9 on composition memetic, because v6 declares
    memetic value independent of content.
  - Narration and puzzle framing score about 0.85 to 0.95 on composition Anticipation and
    Payoff.
  - A checked proof earns nothing extra.

## Changes

1. **Composition (the main lever).** In a composition request, the axis `instructions` are
   replaced, so the edits go into `composition_instructions` and the three
   `composition_axis_instructions`.
   - Comments earn credit only when they state a contract the code realizes.
   - Narration, suspense devices, banners and incantatory prose earn nothing. When prose
     outweighs the code or delays the contract, they lower the rating.
   - Costume vocabulary is translated out and counted as a cost. Costume means a consistent
     themed world that renames the domain's concepts. A short evocative word used as the exact
     name of one operation or type is not costume, so terse figurative operation names are
     not penalized.
   - The v6 clause "decorative/vacuous form does not disqualify memetic" is removed. The
     user's instruction supersedes it, because the evidence requires it.
2. **Memetic becomes the imitable shape of the mechanism,** meaning what a reader would copy
   into new code: a representation, an operation pair with laws, aligned case tables, a law
   paired with its proof, or a recurrence.
   - Costume is judged one level below the same shape named plainly.
   - Plain verbose code with no distinctive shape is Ordinary.
   - Levels 1, 3 and 4 were rewritten. The level-2 sentence for supporting helpers is kept.
3. **Anticipation now comes from the contract:** types, operation names that say what they
   do, and compact equations or one-line invariants.
   - Suspense scores below a plain up-front statement of the same relationship.
   - Names that need decoding through a metaphor withhold the contract.
4. **Payoff comes from definitions that visibly realize the contract.**
   - A checked law or proof, or a law that holds by construction, completes the resolution.
   - A law that is stated but unproved is resolved only as far as the visible code makes it
     evident.
   - Prose answers and reveals resolve nothing.
   - Level 4 now requires the contract to close completely.
5. **Delight penalizes three opposite excesses alike:** prose volume, long names with
   rebinding, and crushed abbreviation.
   - Costume costs more than plain long names.
   - Ornament and pass-through layers cost the most.
   - Rough level anchors are given to keep the order: plain long names > costume and
     narration > crushed or ornamental code. This protects the two duels v6 already gets
     right: costume beating ornament, and narration beating crushed code.
6. **Compression (big brain) is conceptual, not typographic.**
   - Abbreviation, packed lines and deleted laws hide concepts.
   - Costume renaming and pass-through layers add concepts that explain nothing.
   - Narration and reveal framing do not raise the score.
   - Laws that the structure makes true, and short proofs, count as evidence.

No bar, level count or threshold changed. Declaration targets for supporting helpers keep
their level-2 wording.

## Generality

The text never names the tasks, their identifiers or their styles. It describes devices
(costume vocabulary, suspense devices, pass-through layers, crushed abbreviation, stated
laws, checked proofs). The words "algebra" and "collapse" appear only in unchanged v6
sentences.

## Risks

- **d1/d9 (plain verbose code beating costume code)** is the hardest flip, with a v6 gap of
  -0.236. It depends on the costume penalty outweighing the parallel structure of the
  costume code.
- **d3 and d4 could regress** if the judge treats costume the same as ornament, or prose the
  same as crushed code.
- **The memetic redefinition conflicts** with the AGENTS.md and docs/perch-style.md wording
  that memetic appeal is independent of conceptual value. If this candidate is adopted,
  those texts need a matching update.
- **"Stated laws prepare" could reward law comments** that the code does not realize. The
  text says comments count only when the code realizes them, and level 3 still requires a
  meaningful relationship.

## Critic revisions

- **Delight level 0 no longer lists costume.** It contradicted the instruction anchor that places costume at about level 1 and ornament at 0 to 1. That contradiction put at risk the costume-over-ornament ordering the user gave at strength 2.
- **Delight restores the v6 welcome for terse names,** symbolic structure and learned idioms, and restores the list of non-goals. Crushed density now means non-word abbreviation plus packed cases with no stated contract. Short real words and established idioms are not abbreviation. The level anchors apply only when one excess dominates a declaration.
- **Costume now has one definition,** kept once in the shared composition text: a sustained borrowed world, such as a story, myth, ritual, ceremony or unrelated scene, whose names must each be translated back. Two things are exempt: a figurative word that reads directly as the name of one type or operation, and a coined term for a concept the domain lacks. The exemption keeps plain figurative names and a project's own insider vocabulary from being penalized. The composition axis texts refer to this definition instead of repeating it. Each declaration question is sent with only its own instructions, so the Compression, Delight, Memetic and Anticipation instructions each repeat the one-sentence exemption.
- **Memetic text is generalized away from one structure.** "Operation pair", "combinator pair" and the entry-point wording became "family of primitives" and "set of combinators". Contagious (level 3) now requires a pattern beyond the obvious way to write the task, so ordinary tidy code is not lifted. Generative grammar (level 4) no longer requires stated laws.
- **Anticipation level 3 treats stated laws as optional.** Types and operation names can set up a meaningful relationship on their own. Stated laws still strengthen the preparation and remain the route to level 4.
- **Payoff ranks resolution explicitly.** In order: a law checked in code by its proof, then a law that holds by construction, then a law stated only in a comment, which resolves only as far as the code lets the reader verify it. Level 3 keeps "earned recognition".
- **Declaration requests carry only the comment lines directly above a declaration,** as `bendDeclarationSource` shows, so a file-header law block never reaches them. Two changes follow:
  - Compression and Anticipation now say that a declaration need not restate laws given elsewhere in its file.
  - The comparative clause "deleting stated laws" was removed, because a judge reading one version cannot compare.

### Remaining risk from header comments

- Compression still counts stated laws as evidence at declaration level.
- A layout that places its laws directly above the definitions therefore collects that credit.
- A layout that states its laws in a separated file header gets none.
- As a result, composition decides the laws-versus-no-laws and puzzle-versus-plain comparisons almost entirely.
