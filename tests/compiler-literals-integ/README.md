# Integration books: nest merged into the literals line

Increment `literals-integ` merges `campaign/nest` into the literals line (`campaign/literals-layout`).
Neither parent suite pins the behaviors below, which the merge decides. Each is frozen from the pinned
seed (D7) before any Knot lane is compared with it.

| Book | Seed | Knot |
| --- | --- | --- |
| `erased-dotted-let` | accepts `-a.b : Flag = x` and `-a.b = x` with no parameter `a.b` | agree: Checked, evaluator and Wasm return the seed's tag on five calls |
| `arm-body-case`, `arm-body-def` | reject: an orphaned `case`, and a `def` that heads no term | `Invalid parse body-indentation` |
| `spaced-plus-concat` | accepts `two(a ++ b, "ab")` on Strings | `Unsupported parse operator` |
| `literal-column-u32`, `literal-column-offset` | accept a literal or Nat offset in a row of two columns | `Unsupported check literal-column` |

Reading the table:

- Each rejection or refusal is classified, never passed through: `check`, `compile` and `eval` refuse a
  rejected or unsupported book with the frozen exit and diagnostic prefix, `compile` leaves an existing
  output untouched, and no artifact appears (D4).
- An Invalid claim is made only where the seed rejects. A spaced `+` after an argument is Unsupported,
  because `a ++ b` is valid and a parser that called it a missing comma would be Invalid on a valid book.
- The books hold under any D4-safe ruling on the contested constructs of `tests/compiler-literals/REPORT.md`
  ("Integration with nest"). The nest tip answers `erased-dotted-let` and both `arm-body-*` books as the
  merged tree does; the literals tip answers differently (Invalid on the erased let, a false Invalid on a
  valid book; Unsupported term-form for a keyword body). The other three books use `import Base`, which
  the nest tip does not load, so no parent pins them. The contested constructs (dotted binders, layout, a
  spaced `+` in a body, malformed names, enum variable rows) stay in the suites that pin them.
- One book fails under one reading of a contested rule, by design: nest's `argspace-operator-call` reads a
  spaced `+` after an argument as `Invalid parse argument-separator`, and that reading is Invalid on
  `spaced-plus-concat`, a book the seed accepts (the mutant `spaced-plus-is-a-missing-comma` is exactly
  that reading). A ruling for nest's rule must keep `a ++ b` Unsupported.

## Gate

`python3 tests/compiler-literals-integ/freeze.py` verifies `expectations.json` against the seed;
`python3 tests/compiler-literals-integ/check.py` (registered as `literals-integ`) then builds the
`check`, `eval` and `compile` CLIs in both seed lanes and compares every book, and builds six
one-rule mutants of the merged parser and matrix, each of which must change its witness book's verdict
to the one frozen in `MUTANTS`:

| Mutant | Rule it breaks | Witness verdict |
| --- | --- | --- |
| `erased-let-dotted` | an erased let's name is any name | `Invalid parse binding-name` |
| `case-heads-a-body`, `def-heads-a-body` | a keyword heads no arm body | `Unsupported parse term-form` |
| `spaced-plus-is-a-missing-comma` | a spaced `+` may be an operator | `Invalid parse argument-separator` |
| `literal-column-checked`, `offset-column-checked` | a literal column is not checked | `Checked` |

The gate writes only `receipts/literals-integ.json`.
