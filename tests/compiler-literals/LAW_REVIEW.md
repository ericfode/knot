# Literal laws

Contract: [README.md](README.md), unchanged [expectations.json](expectations.json),
the separately committed [supplemental.json](supplemental.json) and the
review-round-1 to round-3 [regressions.json](regressions.json). No law
changes the seed oracle or weakens an existing compiler gate.

| Family | Laws | Proof entry | Obligation |
| --- | --- | --- | --- |
| Algebra and reading | 17 | `src/literal-PROOF.bend` | Division/remainder by zero; wide left/right shifts with explicit `n >= 32` evidence; inhabited boundary 32; String append order, length count and a length-mismatch inequality through the accumulator traversals; an escape before `{` stays an escape; surrogate and scalar sequences; decimal maximum/overflow; full-bit signed LEB; NUL; legacy literal capability boundary |
| Core source machine | 6 | `src/literal-core-PROOF.bend` | Nat literal starts unary materialization; one successor cell; intrinsic argument state; default selection and scope; one String cell |
| Pattern matrix | 6 | `src/literal-matrix-PROOF.bend` | Zero/one offset, Nat/String constructor expansion, stable distinct numeric test order, and a promoted alias promoting only its own column |

Every declaration is a `law` with a filled implementation in its complete proof
entry. The wide-shift proofs use congruence over the guard's Bool decision. The
boundary law supplies a concrete witness for the antecedent. Default scope is
proved by cases over both evaluator value shapes. The remaining equations
reduce definitionally on their stated inputs; they do not assert an induction
that has not been proved.

The law subjects are the actual reader, primitive evaluator, source transition
and matrix helpers. The gate runs each complete proof entry with the pinned
seed and requires exactly `All terms check.`. Existing complete frontend,
checker, runtime, catalog, fields, recursion, Base and loader proof entries
remain exercised by their unchanged campaign gates. The checker entry
(`src/check-PROOF.bend`) gains two rebuild laws: a promoted refined value is
rebuilt with no field uses, and an affine one keeps them.

These laws do not prove the whole parser/checker/emitter correct, the Wasm
interpreter equivalent to the source evaluator, memory separation for all
executions, totality of every intrinsic, or all-input equivalence to Base. U32
operations and List/String helper reductions inherit the seed's trust boundary.
The intrinsic ABI is trusted implementation, explicitly inventoried as
`BaseIntrinsic`. Runtime resource bounds are separate from source validity.

Independent counterexamples are fixed before implementation in the seed
freezes; each review regression book was committed before its fix.
The gate compares seed results to the source evaluator and to emitted Wasm in
both compiler lanes, then kills signed-compare, trapping-divide, masked-shift,
merged-surrogates, offset-off-by-one, spaced-offset, invalid-u32-constructor,
append-reversed, inferred-let-literal, kept-zero-offset,
internal-literal-scrutinee, unsupported-literal-pattern, broad-unicode-escape,
affine-promoted-rebuild and affine-promoted-column mutants. Mutants retain types and must produce the
designated runtime disagreement or classification change; a broken compiler or
incomplete observation is not a successful mutation test. A deliberately false
`append_order` (expecting `[97,99,98]`) is rejected by the proof entry.

Offline style preflight is required on every changed Bend file and the nine new
bounded families. Live Perch coverage and all style axes remain unmeasured in
this offline executor. Deterministic proof acceptance does not imply a style
pass or whole-program refinement.
