# The ladder: where does too much begin?

On 2026-09-27 the user tagged 18 of 28 sampled declarations "fine but generic"
and none "over-styled" or "want more", then said in chat that none of it was
remotely too much, that the edge is much further out, and that all of it was a
little boring to read. The corpus therefore supplies no positive anchor and no
negative anchor. This directory supplies candidates for both.

Five treatments of one figure, the owned time-slicing machine from
`research/adaptive-tasks/task.bend` with its three laws. Every rung checks under
the pinned Bend 2.0.29 (`scripts/bend-reference <file> --check-only`). Nothing
here is production source; the accepted machine is untouched.

| Rung | File | What changes | What stays |
| --- | --- | --- | --- |
| A | [A-tight.bend](A-tight.bend) | One line per arm, aligned columns, each law directly under its mechanism, proof arms mirror the mechanism's arms | Every name and every claim |
| B | [B-held.bend](B-held.bend) | One metaphor throughout: Held, Owed, Kept, give, owe, mete, age, settle | The machine, the laws, the arm structure |
| C | [C-budgets.bend](C-budgets.bend) | Adds give_all over a budget list and two laws, so regrouping is a theorem | Everything in B |
| D | [D-notation.bend](D-notation.bend) | One- and two-letter names, comment rulers as section marks, one-line laws | The machine and all four laws |
| E | [E-past.bend](E-past.bend) | Single letters everywhere, laws l0 to l3, no comments, no blank lines | The machine and all four laws |

## Verdicts, 2026-09-27

| Rung | User | Reading |
| --- | --- | --- |
| A | "boring" | Layout alone earns nothing |
| B | good, still a little dull | One metaphor through the vocabulary is a first positive move |
| C | good, still a little dull | A real added idea with its own laws is a second |
| D | over-styled: "the one letter things are too hard to read" | The edge is abbreviation, not rulers or one-line laws |
| E | over-styled | Past the edge, as intended |

Consequence: push idea density, not notation density. Rung F,
[F-affine.bend](F-affine.bend), reads every frame and the clock tick as an
affine map, so a task is a composition of maps waiting for its seed and `plan`
is the whole task read at once, with one concrete law that stepping and planning
agree. It also checks under the pinned compiler.

The page now compares treatments in pairs, with the current committed code as
one of the seven treatments, and records for each pair which is more fun to
read, whether either is too much, and why. Model review of the rungs waits
until the pair verdicts are recorded.

Rung B's `Purse` type replaced `Word`, which Base reserves; the rename is the
only compiler-driven change.
