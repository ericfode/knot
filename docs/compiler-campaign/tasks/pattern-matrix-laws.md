Excerpt of tests/compiler-nest/SPEC.md: the matrix and decision paragraphs that the pattern-matrix laws state and prove.

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
