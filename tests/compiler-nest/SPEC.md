# Pattern matrices and recursive tree execution

The seed is Bend 2.0.29 at `574b6d39a235b539eb19a5c532993a0abb3d11ad`.
`expectations.json` and its 40 fixtures remain immutable. Every gate starts by
reproducing all 174 seed entry calls with `regen.py`.

The checker accepts ordered multi-scrutinee matches, wildcard and variable rows,
nested constructor patterns, overlapping rows, and empty datatypes. Constructor
patterns resolve at their source declaration event. Bare pattern names are
binders only when no constructor with that name has been declared yet.

A matrix is a list of columns and an ordered list of rows. A variable-only
column aliases its lexical identity without inspecting it or closing earlier
parameters. A constructor column specializes each distinct constructor in order
of first appearance; unmatched constructors use the default rows. Specialization
retains row order. A wildcard row survives every constructor specialization.
When no columns remain, the first row supplies the body. Source pattern names
and arities are validated before body selection, including unreachable rows.
Unreachable bodies are neither resolved nor checked. A constructor pattern
makes its column strict even under an earlier irrefutable row.

Each generated match has one scrutinee and flat field binders. The existing
checker checks type, exhaustiveness, quantity, ordered matching and structural
descent before constructing core `Case` trees. Aliases share lexical levels;
matching refines every name for that level. Reconstruction uses the live field
obligations, including through nested aliases. Promotion can make affine Data
reusable; it cannot make erased fields live. The evaluator and both Wasm
profiles consume the same existing checked core.

Flat, unique single-scrutinee cases retain their original path and byte order.
The 25 enum modules must match their frozen hashes in both native/Bun compiler
lanes and both emitter profiles. A checked zero-row match on an empty datatype
emits `unreachable`; that function has no domain-valid host invocation. This
instruction is distinct from the field arena guard. No new host ABI is added.

Every expanded source match receives 4096 matrix steps. A variable column
spends one; a constructor split divides the remaining steps equally among its
branches, rounding down. Exhaustion is conservative and reports `Exhausted
check budget`. This bounds expansion as well as depth; it is not a total-work
counter for the entire compiler. Existing source, parser/checker depth,
lexical-level, emitter and evaluator limits still apply.

The fields profile executes the three accepted recursive nest fixtures. Their
recursive calls are checked by the [seed decreasing-call rule](../compiler-descent/SPEC.md).
`rec-swapped-args` and `rec-alias` now meet their frozen Invalid check outcomes.
Their frozen codes remain null, so the gate requires Invalid and the check
phase without choosing a diagnostic code. No conservative override remains;
all 40 outcomes must conform and the receipt must set `qualification.complete=true`.
All unexpected mismatches fail the gate.

The added controls have independent seed/literal expectations in
`control-expectations.json`. A depth-12 complete binary tree requires 81,908
bytes for its tree cells plus 100 bytes for the depth value, exceeding the
65,536-byte arena. The seed and evaluator return On; emitted Wasm reports
`Exhausted wasm arena-overflow`. The depth-4 control needs 344 bytes and succeeds.
A wide total matrix exhausts the matrix-step budget. Reusing a reconstructed
nested affine alias must remain Invalid. Rejected/exhausted compilation must
preserve an existing output file.

The gate typechecks six independent compiler mutants and demands the intended
wrong semantic observation in both native and Bun lanes: last-row selection,
specificity sorting, omitted defaults, missing-arm acceptance, erased-field
activation and affine reuse through a nested alias. A type error, timeout,
missing import, invalid module or host failure is not a semantic kill.

Proof scope: stable row-identity selection is universal over source row lists;
irrefutable-column preservation, first-leaf selection, alias identity/erasure
default completion and exhaustion are quantified helper laws. Two complete checker normalizations
exercise an overlapping irrefutable row and an exhaustive 2-by-2 matrix. Those
full-tree witnesses are concrete, not a general compiler-correctness or
exhaustiveness theorem. Runtime differential checks remain separate evidence.
Live Perch review belongs to the coordinator; this increment records offline
preflight without claiming style ratings or automatic qualification.
