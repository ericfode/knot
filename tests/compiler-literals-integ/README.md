# Integration books: nest merged into the literals line

Increment `literals-integ` merges `campaign/nest` into the literals line (`campaign/literals-layout`).
Neither parent suite pins the behaviors below, which the merge decides, and review round 1 found more of
them. Each book is frozen from the pinned seed (D7) before any Knot lane is compared with it: the six books
of the merge, then 47 for the round-1 repairs, each in a commit of its own before the repair, and
`erased-dotted-rebind-shapes`, added after the repair: the four programs of the review's first finding
(`v1`, `v2`, `w3`, `w7`) in the shapes it gave them.

| Book | Seed | Knot |
| --- | --- | --- |
| `erased-dotted-let`, `erased-dotted-rebind`, `erased-dotted-rebind-shapes` | accept an erased dotted let, and a live let of its name below (plain, typed, twice erased, three-part, in an arm, past a second erased let) | agree: Checked, evaluator and Wasm return the seed's tag on every call |
| `erased-then-other-dotted`, `erased-in-other-arm` | reject a live dotted let that no name in scope binds | `Invalid parse binding-name` |
| `arm-body-case`, `arm-body-def` | reject: an orphaned `case`, and a `def` that heads no term | `Invalid parse body-indentation` |
| `spaced-plus-concat`, `let-concat-typed`, `let-concat-untyped`, `let-concat-glued` | accept `a ++ b` after an argument and on the right of a let (typed, untyped, glued) | `Unsupported parse operator` |
| `literal-column-u32`, `literal-column-offset`, `literal-column-late-*` (U32, Nat, offset, Char, String), `literal-column-third`, `literal-column-after-binder` | accept a literal or Nat offset in any column of a row of several | `Unsupported check literal-column` |
| `arguments-literals`, `arguments-name-literal`, `arguments-constructor-literals`, `arguments-field-pattern-literal` | accept literals separated by whitespace in arguments, constructor fields and field patterns | `Unsupported parse argument-whitespace` |
| `promoted-type-{pattern,field,let,let-typed,own-early,nat,string}` | reject `+D` where D names a type declared before it | `Invalid check promoted-type` |
| `promoted-type-{bool,module,imported}` | reject `+Bool` (Base's type outside the reachable slice) and a module's own `+Flag`; accept a fresh `+Flag` in a file that imports one | `Unsupported check promoted-type` |
| `promoted-type-later`, `promoted-function-name`, `promoted-fresh-name`, `binder-type-name-plain` | accept a `+` binder that names no type before it, and a type's name as a plain binder | agree |
| `parameter-shadows-{own-type,type,later-type,result}` | reject a parameter named like the type an annotation after it reads | `Unsupported parse parameter-shadow` |
| `annotation-shadow-{let,erased-let,pattern,parameter}` | reject an annotation that spells a binder in scope | `Unsupported parse annotation-shadow` |
| `parameter-shadow-unused`, `annotation-shadow-unread` | accept binders named like types that no annotation reads, and `Flag : Flag = x` | agree |
| `row-wide-{nat,u32}`, `row-narrow-{literal,nested-literal}` | reject a row wider or narrower than its match | `Invalid check pattern-arity` |
| `qualified-order-lib-{first,last}` | accept qualified constructor patterns whichever file comes first by byte offset | agree |

Reading the table:

- Each rejection or refusal is classified, never passed through: `check`, `compile` and `eval` refuse a
  rejected or unsupported book with the frozen exit and diagnostic prefix, `compile` leaves an existing
  output untouched, and no artifact appears (D4).
- An Invalid claim is made only where the seed rejects and Knot decides why. A spaced `+` after an argument
  or a let's value is Unsupported, because `a ++ b` is valid and a parser that called it a missing comma would
  be Invalid on a valid book. A binder that shadows a type is Unsupported, because a binder may be
  type-valued, which Knot does not model.
- The books hold under any D4-safe ruling on the contested constructs of `tests/compiler-literals/REPORT.md`
  ("Integration with nest"). The contested constructs themselves stay in the suites that pin them.

## Gate

`python3 tests/compiler-literals-integ/freeze.py` verifies `expectations.json` against the seed;
`python3 tests/compiler-literals-integ/check.py` (registered as `literals-integ`) then builds the
`check`, `eval` and `compile` CLIs in both seed lanes and compares every book, checks two more things and
builds 19 one-rule mutants of the merged parser, checker and matrix, each of which must change its witness
book's verdict to the one frozen in `MUTANTS`:

- **Metamorphic stage.** A comment before any module of `tests/compiler-modules/fixtures` (its libraries, then
  its entries) changes no verdict: 42 entries, 84 pairs. Byte offsets order the tokens of one file only.
- **Selfhost twin.** `tests/compiler-selfhost/fixtures/fuel-string-columns-arity` is pinned `reject` there, but
  the suite runs Knot single-file, where the book stops earlier at `Unsupported lex literal`; here its bundle
  entry must answer the pinned `Invalid check pattern-arity`.

| Mutant | Rule it breaks | Witness verdict |
| --- | --- | --- |
| `erased-let-dotted` | an erased let's name is any name | `Invalid parse binding-name` |
| `let-binds-nothing-below` | a let's name is in scope in its body | `Invalid parse binding-name` |
| `case-heads-a-body`, `def-heads-a-body` | a keyword heads no arm body | `Unsupported parse term-form` |
| `spaced-plus-is-a-missing-comma` | a spaced `+` may be an operator | `Invalid parse argument-separator` |
| `let-value-ends-at-any-token` | a `+` after a let's value is an operator | `Invalid parse expected-newline` |
| `literal-starts-no-term` | a literal starts a term (a column, an argument) | `Invalid parse expected-:` |
| `literal-argument-is-a-missing-comma` | the same, in call arguments | `Invalid parse argument-separator` |
| `literal-column-checked`, `offset-column-checked` | a literal column is not checked | `Checked` |
| `parameter-shadows-nothing`, `parameter-shadows-every-name` | a parameter shadows the types its annotations read, and no others | `Checked`, `Unsupported parse parameter-shadow` |
| `annotation-reads-no-binder`, `annotation-reads-every-name`, `arm-binds-no-variable` | an annotation reads the binders in scope, a pattern's variables among them | `Checked`, `Unsupported parse annotation-shadow`, `Checked` |
| `promotion-of-a-type-accepted`, `promotion-of-a-later-type-rejected` | `+D` names a type declared before it, not after | `Checked`, `Invalid check promoted-type` |
| `row-width-unrouted` | a match takes the literal matrix only at width one | `InternalFailure check pattern-node` |
| `declaration-order-by-offset` | a body meets the datatypes declared before it in the book | `Invalid check unknown-constructor` |

The gate writes only `receipts/literals-integ.json`.
