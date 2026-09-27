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

The user tags each rung on the taste-anchor page. The rung where "too much"
begins is the first negative anchor; any rung tagged "want more" is the first
positive anchor. After those verdicts are recorded, and not before, each rung
is reviewed with `npm run lint:style` so the judge's reading can be compared
with the user's on the same five files.

Rung B's `Purse` type replaced `Word`, which Base reserves; the rename is the
only compiler-driven change.
