# C backend law review

The contract is [SPEC.md](SPEC.md). `src/c-LAWS.bend` states eight laws and
`src/c-PROOF.bend` fills all eight. The gate runs the complete proof entry and
requires `All terms check.`. These are checked helper equations, not a proof of
compiler correctness, C memory refinement, or the native compiler.

| Law | Obligation and scope |
| --- | --- |
| `erased_constructor_has_a_cell` | A declared field makes its datatype boxed even when the field is erased. |
| `saved_calls_keep_their_continuation` | A value-producing continuation prevents a self-call from being lowered as a tail jump. |
| `erased_argument_has_no_code_or_slot` | Erased call or constructor arguments advance neither runtime arguments nor temporary allocation. |
| `erased_binding_has_no_initializer` | An erased let does not emit its initializer. |
| `erased_pattern_preserves_offset` | An erased field binding consumes no cell slot. |
| `erased_parameter_preserves_saved_arguments` | An erased parameter advances the source parameter level without consuming a staged live argument. |
| `two_parameters_rebind_before_loop` | Two saved live arguments are assigned before the tail jump. This is a bounded witness, not a universal parallel-assignment theorem. |
| `zero_depth_is_exhausted` | Zero emitter depth yields Exhausted before traversing a core term. |

The independent behavior oracle consists of the unchanged enum and fielded
corpus manifests, the unchanged recursion observations, and the new literal
fixtures in `cases.json`. The seed observations in
`receipts/reference.json` were fixed before C results were observed. Each
recursion observer preserves the complete original source as a byte prefix and
matches every constructor and live field in its expected result. These
observers provide an enum ABI observation of a structured value; the original
structured evaluator result is checked separately.

`tail-rebind.bend` fixes all four inputs for one and two simultaneous swaps.
The decreasing Peano argument and both Flag parameters must move together.
`deep-recursion.bend` copies a 64-node Peano through non-tail recursion before
observing parity. Its restricted-depth build must report Exhausted, while a
64-step tail-recursion control completes at depth 8.

The four C-emitter mutants remain valid Bend and emit compilable C99. A swapped
live-field offset, inverted tag comparison, and skipped accumulator rebind
must return a wrong in-domain ordinal. Removing the arena check must turn an
exact-end allocation followed by one additional slot from exit 4 into exit 0.
That last harness never dereferences the one-past pointer, and all mutant
executables also run under ASan/UBSan. Syntax errors, host failures, sanitizer
failures, timeouts, and out-of-domain results cannot count as semantic kills.

The arena and depth guards are execution evidence. The proofs do not establish
that a C compiler's concrete frame size is below the emitter's conservative
charge, that every possible supported source fits the default resource
budgets, or that any host compiler preserves the C semantics. Exhaustion stays
separate from Invalid and Unsupported. Live Perch semantic and rubric-v8
qualification belong to the coordinator; offline preflight reports structural
coverage and blockers only.

## Public boundary and coverage matrix

| Surface | Checked law or deterministic observation | Remaining boundary |
| --- | --- | --- |
| `c.emit` and the C compile entry | Complete checked loader, 46 corpus books, 11 original recursion books, byte identity in both compiler lanes, rejected-input and exhausted-output artifact preservation | The caller of `emit` must supply checked core. There is no general source-to-C refinement theorem. |
| Generated `knot_export_N` wrappers | Every frozen enum-signatured call reaches its wrapper; live arity and per-type ordinal domains have positive and negative controls | Structured arguments and results stay internal to compiled calls. No external cell-pointer ABI is claimed. |
| `knot_invoke` | Name lookup, unknown/structured export rejection, arity and enum domains are exercised through the generated shim | The null-pointer guards are implementation inspection; the gate does not claim exhaustive malformed C-API caller coverage. |
| `knot_reset` | Each process and arena harness establishes a fresh lifetime; the benchmark worker resets before measured calls | This gate does not independently prove arbitrary reset-after-use sequences or use of pointers across reset. |
| `knot_alloc` | Exact cell-slot boundaries, sanitized allocation corpus, exact-end helper probe, and a semantic missing-check mutant | Bounded arena allocation is not owned-storage reclamation, generation safety, or a complete C memory proof. |
| `knot_enter` / `knot_leave` | Deep non-tail exhaustion, long tail-loop success, large-frame corpus and thousands of repeated completed calls | The frame charge is conservative accounting, not a measured native-frame-size theorem for arbitrary compiler options or host stack limits. |
| Generated `main` | Exact JSON observations and malformed ordinal, domain, arity and export failures | Only the declared pure enum host ABI is covered. |
| `scripts/run-c.py` | Four literal adapter controls: success, unknown export, missing artifact and rejected C source; exact compiler flags/version retained | C compilation and host failures stay separate from source-language Invalid/Unsupported. |

The independent review packet in `receipts/review.json` retains three additional
probes: 256-tag matching, nested matching at that size, and default-depth
exhaustion on a 300-node non-tail recursion under sanitizers. Its input hashes,
embedded source and observations are bounded extra evidence, separate from the
registered gate counts.

New valid core term variants must receive explicit C lowering or an Unsupported
capability result before reaching the current `expression-node` fallback. That
fallback reports InternalFailure for traversal containers that cannot occur as
checked expressions in this profile; it is not the classification policy for
future checked language features.
