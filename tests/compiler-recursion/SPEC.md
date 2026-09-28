# First-parameter structural descent

Profile `knot-structural-recursion-1` extends structural checking and the
independent evaluator. Wasm remains `knot-enum-1`; fielded books are unemitted.

A self-call is supported exactly when its first **checked** argument is a
`Reference` whose lexical level is a field of parameter 0, directly or through
further matches. Scope records strict descendant levels separately from the
ordered match frontier. Parameter 0 itself, fields of other parameters,
reconstructed constructors, computed values and fresh local aliases do not
satisfy this rule. Types, quantities, exhaustiveness and declaration ordering
retain their existing checks. Every other self-call reports
`Unsupported check recursive-call`, including erased self-calls without descent.
Live forward calls and mutual recursion retain `Invalid check forward-live-call`.

Matching a descendant adds its new field levels. Lexical shadowing cannot confer
or remove descent from another identity. An unrelated local binding closes the
match frontier but preserves known descendants; its own fresh level is unmarked.
The result is conservative: even reconstruction of a strict descendant does
not qualify once its checked term is no longer a Reference.

The evaluator needs no new semantic operation: recursive applications enter the
same explicit argument/call machine. Fuel exhaustion reports `Exhausted eval
budget`; it is not a source rejection. The deep control constructs the same
64-successor input within the fixed low budget, separating construction from
the recursive call that exhausts it. Structured host arguments remain unsupported.

## Independent expectations

`cases.json` fixes observations before implementation. `receipts/reference.json`
records the pinned seed runs and the baseline implementation hashes at that
freeze. The gate refuses changed fixture/expectation hashes. Peano values use
user declarations; the seed pretty-printer renders Zero/Succ trees as Nat sugar
(`0n`, `64n`), while Knot displays the literal constructor tree. Both spellings
are fixed independently in the manifest, not converted by a host evaluator.

The seed at `574b6d39a235b539eb19a5c532993a0abb3d11ad` rejects the specified
nondecreasing calls with a decreasing-self-call diagnostic. It accepts
lexicographic descent on a later parameter (`second-descent`), which this rule
deliberately reports Unsupported. The task's stated general-recursion behavior
is not observed at this pin; Knot's requested conservative classification stays
unchanged. Negative reference programs are checked only, never evaluated.

Positive obligations include even (two matches before the recursive call), add,
asymmetric tree mirror (both child fields), list length (second field), direct
descent, field shadowing, preservation across lets, and the deep-input control.
Every negative names a nearby valid fixture. All phases run on both native and
Bun builds; supported values agree with the seed. Compile failures must preserve
an existing artifact. Recursive Wasm execution awaits the fields-wasm merge.

Type-correct mutants admit any self-call, suppress all field propagation, and
suppress nested propagation. Their exact wrong observations, as well as their
seed typechecks, must be recorded. Crashes and timeouts are not semantic kills.
Focused laws cover descent membership, propagation and call admission. They
are not a general termination or compiler soundness theorem.
