# Nest gates: what each round froze

`SPEC.md` states the contract; this file records what each review round froze from the seed and
which mutants its gate kills. The seed is Bend 2.0.29 at `574b6d39a235b539eb19a5c532993a0abb3d11ad`.

`review-expectations.json` freezes 29 copied reviewer programs and 49 seed calls
before repairs. `review.py` checks both compiler lanes, evaluator/Wasm agreement,
rejection in both profiles, preserved output artifacts, the enum whitelist and
seven additional type-correct semantic mutants. `fuzz.py` generates exactly
3,000 programs with random seed 1313166164. Seed and Knot verdicts are compared
independently; accepted inputs also run through the Bend evaluator. Host/internal
failures are gate failures, never language rejection. The gate rejects any false
acceptance or seed-valid program classified Invalid.

`round4-expectations.json` freezes 14 round-4 programs and 32 seed calls before
the rebuilt-descent repair. `round4.py` checks both compiler lanes, evaluator
and fields-profile Wasm agreement, rejection in every phase, and four
type-correct semantic mutants. Each mutant disables the recognizer or drops
one of its conditions: strict descent, the constant's type, or its fields. The
six seed-rejected controls stay `Unsupported check recursive-call`.

`round6-expectations.json` freezes 35 round-6 programs and 59 seed calls
before the detached-brace repair. A constructor's `{` must touch its name in
patterns and bodies: 23 seed-rejected gaps (a space, comment or line break,
including through joined headers, nested fields and multi-scrutinee rows)
report `Invalid parse detached-brace`, and a tab stays `Unsupported lex
whitespace`. Eleven seed-accepted controls keep spaces inside braces, before a
call's parenthesis, after a promotion's `+`, in a type declaration and between
joined columns. `round6.py` checks both compiler lanes, evaluator and Wasm
agreement, rejection in every phase, the frontend and matrix proof entries and
five type-correct semantic mutants: ignoring the gap, comparing lines instead
of offsets, shifting the offset by one, confining the rule to patterns and
extending it to a call's parenthesis. `touches_witness`, `touching_brace`,
`detached_brace` and `joined_brace_witness` in `src/LAWS.bend` state the rule;
the fuzz draws the three gap forms as rare pattern, opener and body atoms.

`round7-expectations.json` freezes 35 round-7 programs and 134 seed calls
before the let-promotion repair. A `+` row re-quantifies only a lambda-case
binder: 12 seed-rejected reuses of a `+` alias of an affine let (through calls,
annotations, constructors, lets of lets, nested aliases, shadowing and
fields) and two reused aliases of an affine parameter without a `+` row report
`Invalid check affine-reuse`, and a `+` row on a `Type`-kind parameter stays
`Invalid check reusable-type`. A `+` row on a let of a `Type`-kind value and
19 other seed-accepted controls (parameter and field promotion, reusable,
erased and shadowing lets) are accepted. `round7.py` checks both compiler
lanes, evaluator and Wasm agreement, rejection in every phase, the matrix
proof entry and three type-correct semantic mutants: promoting let aliases at
the quantity site, promoting every variable column at the promote site and
withholding the mark from parameters. `letalias.py` replays the reviewer's
let/alias generator over random seeds 0 to 1,499 and requires seed and Knot
agreement on acceptance and on every evaluated call. `parameter_alias_promotes`
and `let_alias_keeps_quantity` in `src/matrix-LAWS.bend` state the rule.

`round8-expectations.json` freezes 37 round-8 programs and 150 seed calls
before the Type-kind promotion repair. The seed judges a `+` binder's kind only
where the match frontier binds it. Seventeen seed-accepted programs promote a
`Type`-kind parameter or field and destructure it first (with field reuse,
rebuilt parents, nested and multi-column matches, an inherited field, an empty
datatype and four reviewer generator hits) and are accepted. Fourteen
seed-rejected programs let the frontier bind a promoted `Type` binder: at a
leaf, a default or wildcard row, a let, an inherited field used directly, and
ahead of a later flat match, zero-row match or matrix split; they report
`Invalid check reusable-type`. Two destructurings inside a default region stay
`Unsupported check default-scrutinee`, and four `Data`-kind twins are
accepted. `round8.py` checks both compiler lanes, evaluator and Wasm
agreement, rejection in every phase, the matrix and lowering proof entries
and five type-correct semantic mutants: judging the kind at the promotion and
at a field's binding (the finding), and dropping the leaf, split and zero-row
binding sites. `typekind.py` replays the reviewer's Type-kind generator over
random seeds 0 to 2,999, requires seed and Knot agreement on acceptance, and
evaluates one seeded probe call of every agreed acceptance that promotes a
`Type`-kind binder. Four laws and five whole-checker witnesses in
`src/matrix-LAWS.bend` state the rule and pin each site.

`round9-expectations.json` freezes 80 round-9 programs and 111 seed calls before
the repairs. The seed cannot infer a constructor, so an unannotated let of a
binder that a positive branch refined to one (`v =`, `+v =`, `-v =`, flat or in
a matrix) is `Invalid check annotation-required`; a residual, unsplit, later or
annotated binder and a call stay inferable. Every dotted binder is
`Unsupported parse dotted-binder`, a line break in call or constructor
arguments `line-break`, a second arm on an arm's line `same-line-arm`.
`round9.py` checks both lanes, evaluator and Wasm agreement, rejection in every
phase and twelve mutants; `fuzz.py` draws lets of matched binders.

`round10-expectations.json` freezes 152 round-10 programs and 624 seed calls before
the repairs. The seed reads `+` and `-` as a marker only where a name follows
directly, and `->` as one lexeme. A `+` after a term in a row (`a + b`), a marker
after a let (`+ u = ..`) and a split arrow are `Invalid parse` (`expected-:`,
`detached-marker`, `function-result`); a glued marker, a promotion that starts a
row or follows a comma, and a spaced marker first in a body are accepted.
Whitespace-separated arguments, `++y`, a let split across lines and an arm body
at its `case` column are `Unsupported`. `round10.py` checks both lanes, evaluator
and Wasm agreement, rejection in every phase and 22 mutants; `fuzz.py` draws
spaced `+` atoms.

`round11-expectations.json` freezes 330 round-11 fixtures and 328 seed calls, generated from the templates
in `round11_seed.py`, before the repairs. A dead body's nested matches are audited (unknown constructor, arity,
width, bare constructor, call, promoted datatype or constructor, in six shapes with live twins and lax
controls); `+X` names no datatype declared earlier in the file; a binder hides a datatype of its name from a later
annotation, parameter type, result and field type; a numeral opens a later column and is Unsupported; the layouts
the parser does not model (a case at or left of its match or at the margin, a statement or marked body at another
column, a statement on a let's line, a let split before `:` or `=`, a declaration at another column or on a body's
line) are Unsupported, as is a term after a header's scrutinee, a numeral as a call argument and a `(` that starts
a line in a header (the seed reads it as the next term, not a call). `round11.py` checks
both lanes, evaluator and Wasm agreement, rejection in every phase, all
proof entries and 23 audit, name-rule and shadowing mutants; `round11.py --sweep` runs 18 parser mutants and
`fuzz11.py`, 6,100 fixed-seed programs in six families (names, dead rows, gaps, parenthesized columns, widths, layout)
compared with the seed: 0 false acceptances and 0 false Invalid.
