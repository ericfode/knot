# Structural recursion regression corpus

The current rule is [the seed decreasing-call contract](../compiler-descent/SPEC.md).
It supersedes this corpus's historical first-parameter-only rule. Scope keeps
match-refined bindings and separate local-initializer provenance. Lexical
identity, quantities, exhaustiveness and declaration ordering retain their
existing checks. The evaluator and fields-Wasm emitter execute accepted calls.

The evaluator needs no new semantic operation: recursive applications enter the
same explicit argument/call machine. Fuel exhaustion reports `Exhausted eval
budget`; it is not a source rejection. The deep control constructs the same
64-successor input within the fixed low budget, separating construction from
the recursive call that exhausts it. Structured host arguments remain unsupported.

## Independent expectations

`cases.json` fixes the original observations before implementation. `receipts/reference.json`
records the pinned seed runs and the baseline implementation hashes at that
freeze. The gate refuses changed fixture/expectation hashes. Peano values use
user declarations; the seed pretty-printer renders Zero/Succ trees as Nat sugar
(`0n`, `64n`), while Knot displays the literal constructor tree. Both spellings
are fixed independently in the manifest, not converted by a host evaluator.

The seed at `574b6d39a235b539eb19a5c532993a0abb3d11ad` rejects
`same-parameter`, `other-parameter`, `rebuilt-parent`, `rebuilt-constructor`,
`computed` and `shadow-let` with a decreasing-self-call diagnostic. It accepts
`second-descent` and evaluates its entry to `1n`. These transitions were refrozen
before implementation in `../compiler-descent/receipts/reference.json`.
`expectation-revisions.json` lists each explicitly migrated assertion. The gate
first verifies the original immutable freeze, then applies only revisions that
exactly match the independent new freeze (with the original enum compiler's
field-capability rejection). Neither historical receipt is rewritten.

Positive obligations include even (two matches before the recursive call), add,
asymmetric tree mirror (both child fields), list length (second field), direct
descent, field shadowing, preservation across lets, and the deep-input control.
Every negative names a nearby valid fixture. All phases run on both native and
Bun builds; supported values agree with the seed. Compile failures must preserve
an existing artifact. The enum compiler still rejects checked fielded books. The new descent gate
executes their enum observations through the explicit fields-Wasm profile.

Type-correct mutants admit any self-call, suppress all constructor refinement,
and suppress nested refinement. Their anchors follow the new representation;
the same positive and negative witnesses must still kill them. Their exact wrong observations, as well as their
seed typechecks, must be recorded. Crashes and timeouts are not semantic kills.
Focused laws cover comparison, provenance, scope refinement and call admission. They
are not a general termination or compiler soundness theorem.
