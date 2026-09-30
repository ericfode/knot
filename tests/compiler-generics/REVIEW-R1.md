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
