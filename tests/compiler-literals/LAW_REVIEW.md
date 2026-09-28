# Literal laws

Contract: [README.md](README.md), unchanged [expectations.json](expectations.json),
the separately committed [supplemental.json](supplemental.json), the
review-round-1 to round-8 [regressions.json](regressions.json) and the result
displays in [results.json](results.json). No law changes the seed oracle or
weakens an existing compiler gate.

| Family | Laws | Proof entry | Obligation |
| --- | --- | --- | --- |
| Algebra and reading | 22 | `src/literal-PROOF.bend` | Division/remainder by zero; wide left/right shifts with explicit `n >= 32` evidence; inhabited boundary 32; String append order, length count and a length-mismatch inequality through the accumulator traversals; an escape before `{` stays an escape; surrogate and scalar sequences; decimal maximum/overflow; full-bit signed LEB; section runs of width 2 over five bytes are `[[1,2],[3,4],[5]]`, and `seq` restores seven bytes split at width 3; NUL; legacy literal capability boundary; the displayed Char `'\''` and a String of every escape class read back through the reader as their codes; raw/escaped glyphs on both sides of each boundary |
| Core source machine | 8 | `src/literal-core-PROOF.bend` | Nat literal starts unary materialization; one successor cell; the core of `2n+t` (two Succ constructs around t) builds exactly the cells of a literal's Natural state around t's shared value, in 9 transitions; intrinsic argument state; default selection and scope; one String cell; a record's Char, U32, Nat and String fields display as their literals inside the `Name{a,b}` frame |
| Pattern matrix | 5 | `src/literal-matrix-PROOF.bend` | Zero/one offset, Nat/String constructor expansion and stable distinct numeric test order |
| Dead leaves | 2 | `src/check-PROOF.bend` | A dead leaf's Invalid becomes `Unsupported check dead-arm` at the same phase and location; its Exhausted stays Exhausted |
| Offset expressions | 1 | `src/check-PROOF.bend` | The checker lowers `2n+Zero{}` against an installed Nat to its matrix spelling: two Succ constructs around the checked tail, in any scope |
| Own-type literals | 5 | `src/check-PROOF.bend` | `primitive_type`'s cases: an installed primitive wins for any target and spelling; without it, a Nat literal spelled `Succ` against a target declaring Zero/Succ is `Unsupported check literal-base-type`, one spelled `Zero` against a target declaring only Z/S is `Invalid check unknown-type`, a U32 word is Unsupported against any target, and a literal with no target is Invalid unknown-type, each at the literal's location |

Every declaration is a `law` with a filled implementation in its complete proof
entry. The wide-shift proofs use congruence over the guard's Bool decision. The
boundary law supplies a concrete witness for the antecedent. Default scope is
proved by cases over both evaluator value shapes. The remaining equations
reduce definitionally on their stated inputs; they do not assert an induction
that has not been proved. The display round trips are concrete: `quoted` is a
section of the reader on the listed codes, not on every code, and raw
non-ASCII output is outside Knot's ASCII reader. The display law fails on the
pre-fix evaluator with `InternalFailure eval result-tag`.

The law subjects are the actual reader, primitive evaluator, source transition
and matrix helpers. The gate runs each complete proof entry with the pinned
seed and requires exactly `All terms check.`. Existing complete frontend,
checker, runtime, catalog, fields, recursion, Base and loader proof entries
remain exercised by their unchanged campaign gates. The round-3 column
promotion has no law: the literal-patterns group is at 47968 of its 48000
composition bytes. Three frozen books and a mutant pin it instead. For the
same reason the round-5 dead-leaf helper and its two laws sit in
`check.bend` and `check-LAWS.bend`, beside the checker walk that uses them;
the checker gate runs their proof entry, and the 35 counted here are the
three literal entries only. The round-6 own-type laws sit there too, beside
the checker that calls `L.primitive_type`; checker-laws is at 22435/48000
bytes and literal-patterns is unchanged. Their spellings come from the
matrix's own `M.literal`, so the laws state the case split on the expansion
the seed uses, not on a copy of it. The round-7 offset
law `offset_spelling` sits there for the same reason: `literal-core-LAWS`
cannot import `check.bend` without closing the whole checker into
literal-source-machine. It and `natural_offset` form one chain: the checker
spells `kn+t` as k Succ constructs (`M.literal`, as the matrix does), and
that core builds the literal's Natural cells around the shared tail. Both are
concrete at k = 2; no induction over k is claimed, and the linear cost at
depth rests on the frozen round-7 book and the offset-nat-add mutant. Each
fails on a changed right-hand side (three successors), `natural_offset` at
8 transitions, and `offset_spelling` against the restored `Nat.add`
lowering. The walk order itself (live leaves before
dead ones) has no law; the dead-before-live mutant and the live-arm controls
pin it. The round-8 run laws are concrete at widths 2 and 3; that every run
is at most `width` bytes and that `seq` inverts `runs` for all inputs is not
claimed. The stack bound at module scale rests on the frozen module-width
book and the unbounded-chunk mutant. `runs_are_bounded` fails on a changed
right-hand side and against a `split` that closes a run without reversing it.

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
unlifted-promoted-column, refined-default-binder, all-leaf-invalid,
dead-before-live, invalid-own-primitive, invalid-own-pattern,
unspelled-own-target, offset-nat-add, unbounded-chunk, constructor-tag-display,
quote-blind-escape and raw-delete mutants. Mutants retain types and must produce the
designated runtime disagreement, classification change or, for
offset-nat-add, resource exhaustion against the frozen value. unbounded-chunk
must build the u32-literals book to the gate's bytes and fault its Bun lane
with the pinned stack-overflow message on the module-width book, leaving the
output file untouched; that lane disagreement is its defect. Any other broken
compiler or incomplete observation is not a successful mutation test. A deliberately false
`append_order` (expecting `[97,99,98]`) is rejected by the proof entry.

Offline style preflight is required on every changed Bend file and the nine new
bounded families. Live Perch coverage and all style axes remain unmeasured in
this offline executor. Deterministic proof acceptance does not imply a style
pass or whole-program refinement.
