# Review round 1

Starting head: `9c2c749e`. Both major review-r0 findings are confirmed.
The additive `prechecks/review-r0-expectations.json` freezes the exact reported
sources before any repair, including the two inherited datatype layouts.
Sixteen seed parser/checker observations and fourteen interpreter values were
freshly reproduced with Bend 2.0.29 (`574b6d3`) and Bun 1.3.14. Every accepted
control returns `High{}`. Both unannotated matched-parent aliases fail in the
seed checker with `an annotated term (cannot infer)`. Ordinary variable and
matched-field aliases remain inferable; the annotated parent alias is accepted.
No earlier fixture, expectation, law or assertion is changed.

The proposed repair keeps reconstruction's checking and inference boundaries
distinct, and normalizes layout only at header/type delimiters. Required
delimiters and source-adjacency checks stay in force. These frozen targets are
not yet implemented or qualified by this checkpoint.

Use `export PATH=/Users/ericfode/.bun/bin:$PATH` before the gates: that runtime
is Bun 1.3.14, as frozen by io-host. Keep `BEND_NO_TELEMETRY=1` and use
`KNOT_GATE_TIMEOUT_SCALE=4` for the under-load run.

Commit `690bfc61` lacks a coauthor trailer. Its history is preserved here; a
landing-history correction or recorded exception remains a coordinator action.
Every new commit uses `Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>`.

## Inventory amendment

The boundary repair adds `parse.layout_head` to the reachable frontend.
The pinned seed's `book_load` independently enumerates 49 filled `Def` entries
whose defining module is `lex`, `parse` or `syntax`; the original 48 remain and
the sole new name is `parse.layout_head`. The census independently reports the
same 49 definitions, 57 declarations and three frontend files. Its literal
implementation-count expectation is amended from 48 to 49 in a commit of its
own (D7); no source-language verdict, value or capability assertion changes.
Raw independent names are in ignored `.local/generics/review-r1/frontend-count.json`.

The reviewed approval delta is two law/proof files, six new law statements and
their fills, `generics.variable` and `parse.layout_head`. No new feature class,
dependency profile, package edit or promoted semantic evidence is authorized by
this inventory amendment. The inventory's old recursion-Wasm disposition stays
subject to the coordinator ruling in `RULINGS.md`.

## Repair and bounded verification

Both confirmed major findings are repaired, with no dispute. All eleven
reported seed-valid layouts now check. Both unannotated reconstructed-parent
controls are refused as `Invalid check annotation-required`; the annotated
control, ordinary alias and pattern-field alias check. Monomorphic functions
inside generic books use the same repaired variable boundary. The coordinator's
queued repair of the pure monomorphic checker must enforce the same expected-type
requirement for both nullary and fielded reconstructions before calling its
recursive `Rebuild` path. This worktree does not take that queued increment.

Layout uses `syntax.skip_lines` at grammar boundaries, with lookahead before
applied types and separate handling of parameter lists. `type-parse.flush`
excludes newline tokens from source adjacency. Named and structured parameter
routes inspect the original closer offsets before skipping list layout. Three
additional seed-frozen closer negatives retain Unsupported and preserve
compile artifacts. All original expectations, values, laws and 25 mutants stay
unchanged. Eleven new type-correct restoration mutants cover the two findings
and these adjacency controls.

Eight new universal equations have complete proofs: three variable boundaries,
four layout/closer boundaries and newline exclusion from glue. All nine complete
proof entries pass. They establish these exact helper/boundary observations,
not general parser/checker soundness, recursive reconstruction correctness or
the D21 general obligations, which remain required. The new law domains include
boxed and nullary parents, ordinary and pattern-field aliases, actual declaration
layouts and three rejected closer controls.

Fresh Bun verification passes all 51 frozen checker controls and kills all
eleven new mutants, including five additional witnesses. Raw proof, checker and
mutation evidence stays in ignored `.local/generics/review-r1/`. The full native
and Bun phase/Wasm/mutation qualification follows in the registered gate.
The earlier focused attempts are retained, including the stopped first run and
the newline-glue failures; `docs/perch-review-log.md` records their cause and
the procedure that would have caught it before expensive builds.

The reading hypothesis is an explicit expected-type boundary for reconstruction,
paired with one existing layout primitive and exact boundary laws. Compression,
Delight, memetic identity, Anticipation and Payoff are all unreviewed by the
no-live-review instruction. Offline context coverage does not establish any
numeric style rating or automatic semantic/style pass.
