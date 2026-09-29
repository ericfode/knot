# Literal laws

Contract: [README.md](README.md), unchanged [expectations.json](expectations.json),
the separately committed [supplemental.json](supplemental.json), the
review-round-1 to round-10 [regressions.json](regressions.json) and the result
displays in [results.json](results.json). No law changes the seed oracle or
weakens an existing compiler gate.

| Family | Laws | Proof entry | Obligation |
| --- | --- | --- | --- |
| Algebra and reading | 22 | `src/literal-PROOF.bend` | Division/remainder by zero; wide left/right shifts with explicit `n >= 32` evidence; inhabited boundary 32; String append order, length count and a length-mismatch inequality through the accumulator traversals; an escape before `{` stays an escape; surrogate and scalar sequences; decimal maximum/overflow; full-bit signed LEB; section runs of width 2 over five bytes are `[[1,2],[3,4],[5]]`, and `seq` restores seven bytes split at width 3; NUL; legacy literal capability boundary; the displayed Char `'\''` and a String of every escape class read back through the reader as their codes; raw/escaped glyphs on both sides of each boundary |
| Core source machine | 10 | `src/literal-core-PROOF.bend` | Nat literal starts unary materialization; one successor cell; the core of `2n+t` (two Succ constructs around t) builds exactly the cells of a literal's Natural state around t's shared value, in 9 transitions (the k = 2 witness); **for every k, in any book, and every tail term with a known value, k successors around it return k cells around that value in 4k+c transitions (induction on k, `offset_cells`)**, applied to a tail that calls a book function (`offset_cells_call`: 2 successors, 11 transitions); intrinsic argument state; default selection and scope; one String cell; a record's Char, U32, Nat and String fields display as their literals inside the `Name{a,b}` frame |
| Pattern matrix | 5 | `src/literal-matrix-PROOF.bend` | Zero/one offset, Nat/String constructor expansion and stable distinct numeric test order |
| Dead leaves | 2 | `src/check-PROOF.bend` | A dead leaf's Invalid becomes `Unsupported check dead-arm` at the same phase and location; its Exhausted stays Exhausted |
| Offset expressions | 4 | `src/check-PROOF.bend` | The checker lowers `2n+Zero{}` against an installed Nat to its matrix spelling: two Succ constructs around the checked tail, in any scope (the k = 2 witness `offset_spelling`); **for every count up to 4096 and every tail that checks to a term and its uses, it returns `successors(to_nat(count), term)` with those uses (`offset_lowering`); above 4096 it is `Exhausted check` at the offset (`offset_bound`)**; a constructor of one argument keeps its uses (`single_argument_keeps_uses`, induction on the list) |
| Own-type literals | 5 | `src/check-PROOF.bend` | `primitive_type`'s cases: an installed primitive wins for any target and spelling; without it, a Nat literal spelled `Succ` against a target declaring Zero/Succ is `Unsupported check literal-base-type`, one spelled `Zero` against a target declaring only Z/S is `Invalid check unknown-type`, a U32 word is Unsupported against any target, and a literal with no target is Invalid unknown-type, each at the literal's location |
| Names and offset layout (round 10) | 6 | `src/PROOF.bend` | `parse.bend`'s name and binder rules on concrete tokens: a malformed name (`x.`) is `Invalid parse name` at its token; `malformed` holds for `x.`, `x..y`, `x.1` and `x.1a` and fails for `a.b_1`, `_`, `1.5` and `<eof>`; a dotted pattern binder with no parameter of that name is `Invalid parse pattern-binder`, repeats one without error, and a dotted variable at an expression position binds nothing; the tail of an offset after a newline is skipped (`LiteralTail` on `1n`, `+`, newline, `p`, `:`). Ground instances, not a parser soundness theorem |
| Let binders (round 10) | 2 | `src/qualify-PROOF.bend` | A let binder naming a constructor already registered is `Invalid check constructor-pattern-binder` at its token; one naming a constructor declared later (present in the constructor list, not yet in scope) is accepted and the binding is rebuilt unchanged |

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
the checker gate runs their proof entry, and the 37 counted here are the
three literal entries only. The round-6 own-type laws sit there too, beside
the checker that calls `L.primitive_type`; checker-laws is at 22435/48000
bytes and literal-patterns is unchanged. Their spellings come from the
matrix's own `M.literal`, so the laws state the case split on the expansion
the seed uses, not on a copy of it. The offset laws are two chains that meet in one builder. The round-7 law
`offset_spelling` sits beside the checker for the same reason:
`literal-core-LAWS` cannot import `check.bend` without closing the whole
checker into literal-source-machine. It and `natural_offset` were concrete at
k = 2, and review round 9 found that no law covered the general spelling.
The obstacle was the count. The checker reached the successors through
`M.literal`, which decrements a U32 with `U32.sub` and tests it against the
literal 0. A symbolic count does not reduce there (`U32.sub(U32.inc(c),1) == c`
is not provable by reflexivity, and Base states no Word lemma that inverts the
32-bit adder), so an induction over the count has nothing to stand on. The
lowering therefore converts the count once, `U32.to_nat`, and wraps the tail by
`literal-offset.bend::successors`, which is structural in a Nat. Then
`offset_cells` (literal-core-LAWS) is an induction on that Nat, with the tail
given by its evaluation as a hypothesis (any frames, any fuel, any book, so a
tail may call the book's functions), and
`offset_lowering` and `offset_bound` (check-LAWS) state, for every count and
every tail that checks, that the checker's result is that builder's. Both
directions are exact: `steps(k,c,m)` and the wrapped term are the
implementation's own, and `cells` is the specification of the value. The
transition count `4k+c+m` is linear in k. The k = 2 laws stay as witnesses of
the real checker output and of the literal's Natural cells; the general laws
are not derived from them. Trust that remains: `U32.to_nat` as Base's reading
of the count (a Word fold that the pinned Base defines), and the claim that
recursion through `1n+f(p)` allocates linearly, which the frozen depth books
and the offset-nat-add mutant measure and no law states. Negative controls,
thirteen single mutations in a scratch copy of the tree, each make its proof
entry fail: `offset_cells` fails with three leading transitions per layer, an
extra cell or an extra successor at the base, and a shifted tag;
`offset_lowering` and `offset_bound` fail one successor short, with the wrong
tag, with the bound moved to 4095 or to 4097, with the tail's uses dropped,
with the tail checked unspelled or against no type, and when the below-bound
branch is not the Exhausted result; `single_argument_keeps_uses` fails when
`sequential` drops the head. The laws instantiate the installed Nat
(`nat()`, one datatype), like `offset_spelling`; real catalogs are covered by
the differential runs, not by a law. The mismatch check has no law: the
offset-unchecked-type mutant, which drops it, turns the frozen
offset-expression-mismatch book from Invalid to Built. The walk order itself (live leaves before
dead ones) has no law; the dead-before-live mutant and the live-arm controls
pin it. The round-8 run laws are concrete at widths 2 and 3; that every run
is at most `width` bytes and that `seq` inverts `runs` for all inputs is not
claimed. The stack bound at module scale rests on the frozen module-width
book and the unbounded-chunk mutant. `runs_are_bounded` fails on a changed
right-hand side and against a `split` that closes a run without reversing it.

The eight round-10 laws sit outside the 37 counted above, in the proof entries of the
frontend and the module loader (`src/PROOF.bend`, run by the classification gate;
`src/qualify-PROOF.bend`, run by the modules gate), beside the parser and the qualifier they
describe; the literals gate runs neither. Each has a negative control, eleven single
mutations in a scratch copy of the tree that each make the entry fail on the named law:
the name diagnostic renamed; a name allowed to end in a dot, to have an empty word, or a word
to start with a digit; the guard that spares a token that does not start like a name (a
number, `<eof>`) removed; the binder diagnostic dropped; `parameter_named` ignoring the head; the pattern flag
ignored at a variable; the offset tail read without skipping newlines; the let binder not tested;
and the constructor test made independent of source order. The scope of the dotted-binder rule
(a parameter's own name) and the source order of the constructor rule are pinned on real books
by `binder-scope` and by the `dotted-binder-anywhere` and `constructor-binder-anywhere` mutants,
not by these laws.

The layout round adds four ground-instance laws, also outside the 37. Three are in
`src/PROOF.bend`: `list_across_lines` (a call whose items stand across line breaks after `(`,
before and after `,` and before `)`), `arm_across_lines` (a line break after `case` and before
the `:`, with the body at any position `at`, so no body column is checked) and
`cases_right_of_parent` (under a `case` in column 4, a match written in column 2 takes no case
in column 4). One is in `src/check-PROOF.bend`, run by the checker gate:
`binders_meet_registered_constructors` (a single file's `Late` is a pattern binder before its
type and not a let binder after it). Nine negative controls, one mutation each in a scratch
copy, make the entry fail on the named law: the line break kept after an item, after `(` or
after `,` (`list_across_lines`); after `case` or before its `:`, or the old arm-body column
check restored (`arm_across_lines`); the floor dropped from a nested match
(`cases_right_of_parent`); and the constructor test disabled or registration unordered
(`binders_meet_registered_constructors`). These are instances, not a parser theorem: that
every layout the seed accepts parses, or that the parser's structure equals the seed's for
all dedented bodies, is not claimed. The frozen layout books and six mutants pin real books.

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
unspelled-own-target, offset-nat-add, offset-one-short, offset-unchecked-type,
offset-extra-successor, unbounded-chunk, constructor-tag-display, quote-blind-escape, raw-delete,
and the eight round-10 verdict mutants (offset-newline-kept, names-unread, name-may-end-in-dot,
name-word-may-be-empty, name-word-may-start-with-digit, dotted-binder-anywhere,
let-binder-unchecked and constructor-binder-anywhere), and the six layout-round verdict mutants
(case-line-kept, item-line-kept, parameter-line-kept, arm-column-checked, floorless-match and
binder-looked-up). Mutants retain types and must produce the
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
