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

A split's field binders are those of the first row that starts a constructor, as in the seed's `match_flatten`:
a `+` on one of them marks that field in every row below the split, and at every later split of the remaining
rows (`M.leading`, `M.marked`); a `+` in a later row marks only its own binder, and the marks of a variable row
reach every row of its column.

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

Every row of every match is audited, reachable or not. The seed reads the whole book before
checking any body, so each row has one pattern per scrutinee and valid patterns wherever it
sits, in a discarded body too: a declared constructor, its field count, no constructor as a
bare binder, no call, no `+` before a datatype declared earlier in the file. Bodies the lowering
drops are not type-, scope- or scrutinee-checked. A binder hides a datatype of its name from
the types written after it: an annotation, a later parameter type, the result, a later field
type. What each gate froze, with its mutants, is in [ROUNDS.md](ROUNDS.md).

A new source match on a binding narrowed by an earlier default currently
reports `Unsupported check default-scrutinee`. Carrying arbitrary residual
constructor sets through such nested source matches is a subsequent increment;
internal matrix remainders are handled here.
