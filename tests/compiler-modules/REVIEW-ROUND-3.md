# Modules review round 3

The six confirmed findings are fixed. Each has seed observations frozen in
[`review-round3.json`](review-round3.json) before its repair, and every
earlier fixture and expectation is unchanged. Branch `campaign/modules` first
merged main at `574945f` (io-abi-2, io-host, poly, selfhost), with the census
inventory regenerated rather than merged.

| Finding | Freeze | Repair | Disposition and evidence |
| --- | --- | --- | --- |
| A module over 65,537 bytes is truncated | `e44c63a` | `eb5febb` | **Fixed.** The budget now counts UTF-8 bytes. The entry, module and Base tails are `Exhausted lex budget` (before: Checked, Lit). A 65,536-byte ASCII control still loads and runs, and 65,537 bytes stays Exhausted. |
| Adapter bytes are not pinned | `5a71c88` | `fefa100` | **Fixed.** The gate compares the wrapper and both adapters with `host_query_sha256`, requires the adapters to equal the io-abi-2 reference bodies and their pins, and rejects unpinned host files. Six literal controls run every time, and a live flipped byte fails the gate. |
| `import Base#c` / `import Base#` accepted | `f93cb56` | `ca57f6e` | **Fixed.** A `#` begins a comment only at a word start or after the alias identifier. Both spellings are `Invalid load import-alias`, and the seed-accepted `as F#x` still runs to Lit. |
| BOM, FF, NBSP, VT in a header give Invalid | `ed34f42` | `ca57f6e` | **Fixed.** Until the header closes, a line outside printable ASCII, space and tab is `Unsupported load header-character`. The four two-import programs report it at row 1 (before: Invalid import-after-declaration). |
| Binder named like a later constructor is Invalid | `5f39b2b`, `a1d6d46` | `4d5fc75`, `c2722cf` | **Fixed**, including field binders. Binders meet only constructors registered before them. Arm binders reach `Unsupported check variable-pattern` in entry and module spellings. The field-binder variants now run to Lit: a later constructor, and a bare constructor of another module. |
| Let binders `True = x` / `Off = x` accepted | `8732626` | `4d5fc75`, `ea5d482` | **Fixed.** Plain, reusable and typed let binders are `Invalid check constructor-pattern-binder`, for Base and local constructors, in module lanes and, for the single file, in plain lanes. A let named like a later constructor, or `True = x` in a module loaded before Base, still runs to Lit. |

## Mechanism

`load.within` charges each character its UTF-8 width. Decoding never shortens
input (a malformed subpart becomes one three-byte U+FFFD in both seed lanes), so
text within the budget was read whole. The text argument leads, as the seed's
descent check requires.

`imports.words` accumulates reversed words and stops at a `#` that begins a word.
`import_words` ends an alias at its identifier. `printable` guards every line
while the header is open, so the import decision is never made on characters
Knot does not classify.

In `qualify`, the binder inventory starts with the loaded globals' constructors
and gains each datatype's constructors at its declaration (`visible`). Let
binders pass through the same `pattern` check. Single files have no
qualification pass, so `qualify.rebinds` walks one work list in declaration
order over let, arm and flat field binders. `driver.check_file` runs it before
the checker in every single-file CLI path.

The checker's book-wide field-binder test in `patterns.bend` is removed, with
the catalog helpers it used. It ignored declaration order, and in module books
it matched bare constructors across namespaces (frozen `field-cross-module-ctor`).

The pass first lived in `check.bend` as the finding suggested. That pushed the
`checking` manifest composition to 50,315 bytes, over the perch-context gate's
48,000-byte bound, so the pass moved beside the module rule it mirrors
(`ea5d482`). `check.bend`, `check-LAWS.bend` and `check-PROOF.bend` are byte-equal
to the merge base.

## Laws, fixtures and mutants

There are eight new filled laws (89 in the four proof entries: loader/path 28,
qualification 26, Base selection 20, pin helpers 15). Each was checked alone (its
LAWS/PROOF pair reduced to that law) in a scratch copy: it prints `All terms
check.` unmutated and fails at its own location under its matching mutation,
the single-file law under both the let and the arm mutation:

- `budget_counts_utf8_bytes`
- `multibyte_source_is_bounded_by_bytes`
- `glued_hash_stays_in_the_path`
- `glued_hash_ends_an_alias`
- `header_separator_outside_ascii_is_unsupported`
- `later_constructor_leaves_a_binder`
- `let_binder_cannot_rebind_a_constructor`
- `file_binders_meet_only_earlier_constructors`

These are helper/transition laws, not a theorem of compiler correctness.

Round 3 freezes 26 seed fixtures, one seed call each: five byte-budget, three
glued-hash, four header-separator, two binder-order, nine let-binder and three
field/arm-binder cases. Five of
them also run the single-file CLIs in both lanes (30 plain observations).

The gate has ten new semantic mutants, all type-correct under the seed and
killed by frozen witnesses:

- `source-budget-counts-characters`
- `import-comment-splits-anywhere`
- `alias-keeps-glued-comment`
- `header-character-ignored`
- `constructor-order-ignored`
- `let-binder-unchecked`
- `file-let-binder-unchecked`
- `file-constructor-order-ignored`
- `file-arm-binders-unchecked`
- `field-binder-book-wide`

`pattern-global-ctors-dropped` is retargeted to the new initial inventory, with
the same witness and result.

## Merge integration and shared code

The selfhost gate arrived from main after round 2. Its three src mutants
required the seed's foreign-free `All terms check.` and copied no `src/host`.
`3761aa9` applies round 2's seed-derived amendment (compare the exact
foreign-dependency verdict pinned in `host-check-expectations.json`, copy
`src/host`). Every selfhost case's status and Knot observations are unchanged.

The field-binder repair removes a check from `patterns.bend` and two helpers
from `catalog.bend`, code from the fields increment. The compiler-fields
fixture `constructor-name-binder` keeps its frozen Invalid outcome through the
single-file pass. No other gate's mutation site changed.

## Preflight

All preflights are offline, with no provider requests.

- The manifest has 23 groups and 1,375 declaration occurrences. All 23
  compositions are available, with zero truncated or role-limited declarations
  and zero structural blockers. `checking` is 47,400 bytes, under the
  48,000-byte bound.
- The direct invocation covers the eleven changed implementation, law and
  proof files: 326 declarations. It has 55 truncated or role-limited contexts
  (10 caller/byte, 9 file, 36 helper limits) and an oversized combined
  composition, giving 56 structural blockers.

No style rating or style pass is claimed.

## Known limits

The byte budget can report Exhausted for a file within 65,536 bytes whose
invalid UTF-8 expands on replacement. That file would otherwise be Unsupported
non-ASCII.

The header classifier is conservative:

- It rejects any non-ASCII or control character while the header is open,
  including in comments the seed accepts.
- A CRLF module becomes Unsupported at the header rather than at the lexer.

Nested field binders are checked by qualify in module books; single files leave
them to the checker's Unsupported nested-field-pattern. Function parameters named
like constructors (`def f(Off: Flag)`, `+Off`, `True` after `import Base`) are
accepted by the seed, so they are not binder-checked; three probes agree.

The selfhost suite's `modules` and `packages` needs stay unflipped. Landing them
(adding `--bundle` to that gate's Knot lanes) is the coordinator's merge decision.

Live Perch review remains with the coordinator.
