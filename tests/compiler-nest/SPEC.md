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
a reference, so `case a.b:` is `Invalid parse pattern-binder`. Dotted
parameters, fields, definitions and erased let names remain names, as in the
seed.

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
first-parameter rule. The complete seed decreasing-call rule remains outside
this increment. `rec-swapped-args` and `rec-alias` therefore remain explicitly
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
the general exhaustive-lowering law. Two complete checker normalizations
exercise an overlapping irrefutable row and an exhaustive 2-by-2 matrix. Those
full-tree witnesses, now `irrefutable_lowering_witness` and
`exhaustive_matrix_witness`, are concrete. The general irrefutable-first-row and
exhaustive-lowering laws remain **unmet** in `state.json` and `CONTRACT.json`.
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

A new source match on a binding narrowed by an earlier default currently
reports `Unsupported check default-scrutinee`. Carrying arbitrary residual
constructor sets through such nested source matches is a subsequent increment;
internal matrix remainders are handled here.
