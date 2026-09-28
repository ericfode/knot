# Pattern matrices and recursive tree execution

The seed is Bend 2.0.29 at `574b6d39a235b539eb19a5c532993a0abb3d11ad`.
`expectations.json` and its 40 fixtures remain immutable. Every gate starts by
reproducing all 174 seed entry calls with `regen.py`.

The checker accepts ordered multi-scrutinee matches, wildcard and variable rows,
nested constructor patterns, overlapping rows, and empty datatypes. Constructor
patterns resolve at their source declaration event. Bare pattern names are
binders only when no constructor with that name has been declared yet. A name
is words joined by dots, each word a letter or `_` followed by letters, digits
or `_`; the lexer rejects any other word that opens like a name (`Invalid lex
name`). A pattern binder, like a live let binder, is one word: a dotted name is
a reference. The seed accepts one where it rebinds a name in scope, and the
parser does not resolve scopes, so every dotted binder (a pattern, a `+`
promotion, a let, a typed let) is `Unsupported parse dotted-binder`, never
Invalid. Dotted parameters, fields, definitions and erased let names remain
names, as in the seed.

A matrix is a list of columns and an ordered list of rows. A variable-only
column aliases its lexical identity without inspecting it or closing earlier
parameters. This also applies to the latest let binder. `_` is anonymous in
both row and field positions; `_x` is an ordinary name. Commas and spaces are
accepted between scrutinees and between patterns. A match or case header runs
to its colon; line breaks and comments inside it separate nothing.

A constructor column splits on its first constructor. The positive matrix
specializes matching and variable rows, retaining order. The negative matrix
removes that constructor's rows and narrows its available constructor set;
the scrutinee remains a live unrefined binding. Variable rows are checked even
when that set is empty. A missing arm is dead code, as in the seed's
`ctx_dead`, when a live binder in context has an empty constructor set: an
emptied residual or a binder of a zero-constructor datatype. The context is
every binder outside the pending suffix of the match frontier that starts at
the scrutinee: parameters before it, and fields, which join the frontier ahead
of the remaining parameters. An empty binder still pending after the
scrutinee, or an erased one, does not establish this fact. Every
selected body still undergoes scope, type and quantity checking. When no columns
remain, the first row supplies the body. Only bodies shadowed at that leaf are
discarded. Pattern names and arities are validated before body selection.

Each generated decision has one scrutinee and flat positive field binders. The
checker checks both branches before coalescing the binary spine into existing
core `Case` trees. A terminal default is checked once and then shared across its
remaining runtime constructors, with their field layouts. Aliases share lexical levels;
matching refines every name for that level. Reconstruction uses the live field
obligations, including through nested aliases. Promotion can make affine Data
reusable; it cannot make erased fields live. The evaluator and both Wasm
profiles consume the same existing checked core.

Flat, unique single-scrutinee cases retain their original path and byte order.
The 25 enum modules must match their frozen hashes in both native/Bun compiler
lanes and both emitter profiles. A checked empty case emits `i32.const 0`; it has
no domain-valid execution. The enum whitelist is unchanged and is checked on
every enum-profile nest module. The field arena guard remains the only
`unreachable` in the fields profile. No new host ABI is added.

Every expanded source match receives 4096 residual-matrix visits, including
leaves and empty remainders. `Expansion` returns the unused work; the positive
branch's remainder funds the negative branch. There is no division by width.
Exhaustion reports `Exhausted check budget`. The counter bounds total expansion
for one source match, not total compiler work. Separately reached source matches
start separate quotas. Existing source, expansion/checker depth, lexical-level,
emitter and evaluator limits still apply.

The fields profile executes the three accepted recursive nest fixtures. Their
recursive calls descend through nested field patterns using the existing
first-parameter rule. A matched binder referenced again is rebuilt from its
fields, so a variable row reached through an earlier row's nested pattern
passes a constructor, not a reference. Such a rebuilt first argument descends
when it denotes a strict descendant of parameter 0: the refinement of that
level, unfolded layer by layer, has the same type and tag at every constructor
and the same levels in the same field positions. The same holds for a value a
source expression rebuilds. The emitted argument is unchanged. A reference
first argument still takes only the reference rule. The complete seed
decreasing-call rule remains outside this increment. `rec-swapped-args` and `rec-alias` therefore remain explicitly
**unmet**, reporting `Unsupported check recursive-call`. Their frozen Invalid
expectations are unchanged. They are monitored separately and never counted
as conformance passes. The gate may complete its authorized bounded scope with
those two outcomes pending; its receipt must set `qualification.complete=false`.
All other unexpected mismatches fail the gate.

The added controls have independent seed/literal expectations in
`control-expectations.json`. A depth-12 complete binary tree requires 81,908
bytes for its tree cells plus 100 bytes for the depth value, exceeding the
65,536-byte arena. The seed and evaluator return On; emitted Wasm reports
`Exhausted wasm arena-overflow`. The depth-4 control needs 344 bytes and succeeds.
A wide total matrix exhausts the matrix-step budget. Under binary expansion its
13 independent strict columns require `T(0)=1; T(n+1)=2+2*T(n)`, or 24,574
matrix visits. This literal derivation independently justifies the unchanged
`matrix-work` exhaustion expectation. The depth-13 unary, 13-column/two-row,
14-constructor/depth-3 and compiler self-shape controls are linear-size and must
be accepted. Reusing a reconstructed
nested affine alias must remain Invalid. Rejected/exhausted compilation must
preserve an existing output file.

The gate typechecks six independent compiler mutants and demands the intended
wrong semantic observation in both native and Bun lanes: last-row selection,
specificity sorting, omitted defaults, missing-arm acceptance, erased-field
activation and affine reuse through a nested alias. A type error, timeout,
missing import, invalid module or host failure is not a semantic kill.

Proof scope: stable row-identity selection is universal over source row lists;
irrefutable-column preservation, first-leaf selection, alias identity/erasure,
one step of the live split's remainder (the split constructor leaves the
remaining tags and its rows leave the negative matrix; other tags and variable
rows stay) and work exhaustion are quantified helper laws. They do not state
the general exhaustive-lowering law. `irrefutable_first_row_selected`
(`src/lowering-LAWS.bend`, filled in `src/lowering-PROOF.bend` and checked
through the `src/matrix-PROOF.bend` entry) composes them over the complete
lowering: for every fuel, catalog, scope, work budget,
column list and trailing rows, a first row of one variable or promotion per
column whose body is a leaf is the body at every leaf of each successful
`M.expand` tree. Two complete checker normalizations exercise an overlapping
irrefutable row and an exhaustive 2-by-2 matrix; `irrefutable_lowering_witness`,
`irrefutable_first_row_witness` and `exhaustive_matrix_witness` are concrete.
The general exhaustive-lowering law remains **unmet** in `state.json` and
`CONTRACT.json`.
Additional checked helpers cover anonymous lookup, live residual references,
empty-type evidence, latest-let aliases and total-counter leaves. Runtime
differential checks remain separate evidence.
Live Perch review belongs to the coordinator; this increment records offline
preflight without claiming style ratings or automatic qualification.

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
`Type`-kind binder. In `src/matrix-LAWS.bend`,
`destructured_promotion_is_unbound`, `later_match_binds_promotion`,
`leaf_binds_promotion` and `leaf_closes_frontier` state the rule on the
frontier, and five whole-checker witnesses pin each site: a destructured
promoted parameter and field check, and returning the binder, a later matrix
split and a later zero-row match are each rejected.

`round9-expectations.json` freezes 73 round-9 programs and 101 seed calls before
the repairs. The seed cannot infer a constructor, and in a positive branch it
substitutes a matched binder by its constructor. An unannotated let of a
refined binder (flat or in a matrix, through an alias, a nested field or an
enclosing match; `v =`, `+v =`, `-v =`) is `Invalid check annotation-required`;
a residual, unsplit, later or annotated binder and a call stay inferable. Every
dotted binder, including a rebound one that the seed accepts, is `Unsupported
parse dotted-binder`. `round9.py` checks both lanes, evaluator and Wasm
agreement, rejection in every phase and nine mutants. `fuzz.py` draws lets of
matched binders: 36 false acceptances before the repair, 0 after.

A new source match on a binding narrowed by an earlier default currently
reports `Unsupported check default-scrutinee`. Carrying arbitrary residual
constructor sets through such nested source matches is a subsequent increment;
internal matrix remainders are handled here.
