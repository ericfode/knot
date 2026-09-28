# Structural terms and field binding contract

Profile `knot-structural-terms-1`, seed Bend 2.0.29 at
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. This extends the declaration catalog
and preserves the `knot-enum-1` source-to-Wasm subprofile.

Extend the existing monomorphic catalog with constructor arguments and nested
constructor patterns whose fields are plain or `+` binders, including ordered
multi-scrutinee matches. Rows preserve source order; duplicate constructor
rows select the first body. Every argument is
checked against its field's type and demand; erased arguments are checked but
not executed. Constructor expressions still require an expected type. Nested constructor rows specialize their fields before selecting a body;
structural recursion follows its separate descent contract.

A pattern field receives the product of declaration quantity and scrutinee
quantity. A `+` pattern mark may promote quantity 1 over Data to quantity 2;
quantity 0 stays erased. Field names may shadow parameters or earlier fields.
Global constructor names cannot be used as bare field binders. Each occurrence
uses its lexical identity, not its display name.

Matching replaces the scrutinee in the match frontier with its field binders.
For an affine parent, reconstruction spends the live affine field obligations;
it does not retain a second owning alias. A reusable parent supplies reusable
Data fields. Uses of the matched parent reconstruct it from those fields. Further matching of a field refines every reconstruction
which refers to that lexical identity. Sequential affine use sets are disjoint;
alternative sets join. Local field identities are removed at the branch boundary.

The ordered frontier of matchable identities is distinct from allocation order.
Matching drops earlier unmatched parameters, replaces the parent position with
the fields in declaration order, and retains later parameters. Local lets close
the frontier. This preserves the pinned Bend surface restriction.

Checked structural terms and independent tree evaluation do not establish a
heap implementation. The emitter must reject fielded books until owned storage
and lowering exist. Resource exhaustion is distinct from Invalid or Unsupported.
The enum corpus remains the regression oracle. Field runtime storage, transfer,
drop, structural recursion and GPU qualification remain milestone-1 obligations.

## Observations and bounds

`check.check(depth,syntax)` returns a complete checked book or an explicit
error. Checked terms carry field signatures and declaration-ordered arguments;
branches carry stable lexical IDs and effective field quantities. The public
checker CLI exposes these through its canonical `Checked` display. Every
function body is checked, including unused bodies. Invalid field bodies take
precedence over the emitter's later capability rejection.

`eval.invoke(book,name,ordinals,fuel)` interprets the checked core with an
explicit continuation machine. Values are persistent model trees, not owning
heap cells. Constructing fields evaluates live arguments left to right and
skips erased arguments entirely. Unpacking walks declarations while consuming
only live slots. Refined source parents are already reconstructed checked terms.
Returned objects contain live fields in declaration order. `eval.describe`
prints that projection; an all-erased `Ghost{On{}}` prints `Ghost{}`. This is
not the seed interpreter's full source-value display. Equality tests use enum
observations or explicit full/live expected values, with this distinction named.

The evaluator's external arguments remain nullary constructor ordinals. A
fielded constructor ordinal produces `HostFailure invoke structured-argument`;
the caller must create structural values in source. Error/status codes retain
the enum contract. Compiler rejection leaves existing output untouched.

Catalog maxima remain 256 types/functions/constructors/fields/parameters in
their respective scopes. Lexical IDs are bounded to 0..4095; adding at next ID
4096 reports Exhausted before incrementing. Parser/checker depth and evaluator
transition fuel are explicit budgets. Display has a separate work budget of
4096 worklist transitions and a 65,536-character output cap. It reports
`Exhausted inspect`, never truncated success; shared subtree expansion consumes
that same total budget. A terminal return
requires no further transition. Bounded helpers and list scans still depend on
the seed runtime's stack; no machine-stack or complexity improvement is claimed.

The structural equality and quantity fixtures are finite conformance evidence.
Focused helper laws do not establish a general checker-soundness, ownership,
heap-refinement, termination or compiler-correctness theorem.
