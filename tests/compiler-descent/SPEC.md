# Decreasing self-calls

This extends `knot-structural-recursion-1` to the complete decreasing-call rule
for Knot's checked monomorphic first-order terms. The reference is
`bend2/bend.ts::term_descend` and the live `Ref` case in `term_infer` at seed
`574b6d39a235b539eb19a5c532993a0abb3d11ad` (lines 3147–3186 and 3239–3250).
Expectations and seed observations are fixed before implementation in
`expectations.json` and `receipts/reference.json`. `freeze.py` verifies them
without running Knot. The original recursion freeze remains historical evidence.

## Rule

Compare each actual argument with its original parameter, refined by the
matches enclosing the call. Read parameter columns left to right. Skip erased
parameters. Continue through equality, accept at the first strict decrease,
and reject an incomparable/increasing column or an entirely equal argument
list. Columns after a strict decrease impose no termination constraint.
Dead occurrences do not require descent; they still undergo scope, type and
quantity checking. A live all-erased or zero-argument self-call cannot decrease.

The structural comparison has three results: `EQ`, `LT`, and `GT`. Here `GT`
means that equal-or-smaller was not established; it is not a total size order.

1. Strip annotations and follow local aliases for comparison only. A function
   application remains opaque, including an application of an identity function.
2. A variable column is equal only to the same lexical identity.
3. Equal constructor identities and arities compare their fields componentwise.
   Every field must be equal-or-smaller; any strict field makes the whole
   constructor smaller. These fields are **not** compared lexicographically.
   Compare erased constructor fields too; only erased parameter columns skip.
4. If constructor alignment fails, compare the whole argument with each field
   of the column. Equality or descent in any such field makes it strictly
   smaller than the column. Match the seed's search exactly: skip the first
   field that failed componentwise alignment, if any.
5. Every remaining comparison is `GT`.

Consequently `S{x}` versus `S{x}` is equal, `S{x}` versus `S{S{x}}` is smaller,
and `Pair{x,y}` versus `Pair{S{x},y}` is smaller even though it is not a literal
subtree. `Pair{x,S{y}}` versus that same column does not decrease. A fresh local
alias of `x` preserves its structural meaning but retains its own runtime
identity and quantity obligations. Pattern aliases already share identities.
No initializer substitution may bypass affine-use checks.

## Outcomes and boundaries

A checked live self-call that fails this rule reports
`Invalid check recursive-call`. Exhaustion while resolving aliases, rebuilding
columns or comparing shapes reports `Exhausted check budget`; it is not Invalid.
Host/internal failures retain their own categories. Unsupported syntax such as
generics and literals is still rejected by its existing specific frontend code,
before this rule runs. This increment adds no generic/literal approximation.

The seed inspects its pending raw argument spine before typechecking arguments;
Knot checks arguments first. Multiply-invalid calls may therefore report a
different Invalid code. This contract pins the decreasing-call decision for
otherwise checked supported arguments, not identical diagnostic precedence.
Forward/mutual call rules, evaluator fuel, fields-Wasm arena limits, and the
structured-host-argument restriction are unchanged.

## Independent evidence

The fixture family covers second/third columns, earlier growth/shrink, equal
calls, constructor equality/decrease, componentwise growth, same/different-head
subterms, refined parents, alias chains and shadowing, computed aliases, erased
columns/fields, and dead self-calls. New accepted fixtures return a literal
enum, so both compiler lanes can compare the seed, independent evaluator and
actual Wasm execution. The original `second-descent` returns a structured value;
`second-descent-observer` preserves its source (renaming only its entry to
`sample`) and adds a checked enum observation for Wasm. The original program is
also checked, evaluated and compiled directly.

Ten legacy transitions are frozen separately. The seed accepts `second-descent`
and rejects `other-parameter`, both nest recursion negatives and the checker
recursive-call fixture. Historical Unsupported observations do not override
these seed observations. Each migrated assertion receives its own checkpoint.

Required type-correct mutants reverse parameter order, treat equality as a
decrease, and accept descent merely because a reconstructed constructor contains
a smaller field. The last mutant must reject the unchanged `rebuilt-equal`
expectation. Additional controls cover alias opacity, product versus
lexicographic comparison, erasure and resource exhaustion. Proofs state the
comparison algebra and concrete call boundaries; they are not a general
termination or compiler-refinement theorem.
