# Generic checking and erasure review

The fixed task is the seed-derived generic/quantity corpus in `expectations.json`
plus the two supplements committed before implementation. Accept generic headers,
instantiate parameter domains and results, check erased arguments, preserve
quantity restrictions, and use one boxed representation for generic families.
The boundary corpus records seed observations for adjacent syntax and kind cases.
No original fixture, pinned outcome or existing gate assertion changes.

The reading hypothesis is a small type-expression algebra shared by catalog and
term checking. A sequential substitution list instantiates every dependent
parameter domain and result. Rigid binder indices preserve phantom distinctions.
The checked expression projects into the existing runtime once, through erasure.
An erased representation marker gives every generic family a cell, including
nullary constructors, while preserving live signatures and field order.

| Obligation | Checked law / boundary | Independent control |
| --- | --- | --- |
| Substitution composes | `lookup_composes`, `substitution_composes`, `substitution_identity` | Nested box, rigid phantom, interleaved arguments; skipped-substitution mutant |
| Quantity meet is associative, commutative and idempotent | Three `meet_*` laws over every `Q`; literal normalization and identity/absorber laws | Meet-family seed fixtures; wrong-quantity-meet mutant |
| Application erases type arguments | `application_erases_argument`, `parameter_retains_quantity` | Five literal export arities; kept-erased-argument mutant |
| Generic nullary constructors use cells | `generic_nullary_is_boxed`, generic constructor/branch memory laws | Phantom, erased-field and nullary seed calls |
| The marker adds no live signature slot | `marker_retains_live_signature` | ABI arities and native/Bun module identity |
| Erased evaluation steps commute | `erased_argument_commutes`, `erased_field_commutes`, `erased_pattern_commutes` | Independent seed/evaluator/Wasm calls, erased-value fixtures |
| Arity is checked before substitution | Catalog application dispatch | Extra type argument negative; missing-arity-check mutant |
| A bare family name has no arguments | `bare` resolves only a parameterless family; quantity defaults need `Name<..>` | Six seed-rejected bare-family fixtures; bare-quantity-default mutant |
| Unsupported forms never bypass checking | Parser/catalog/term boundaries | Closure/template pins, live type values, type-variable application and constructor-local type fixtures |

`src/types-PROOF.bend` fills all 12 algebra laws. The substitution proof is an
induction over expressions with a separate lookup/composition lemma; it is not
limited to fixture instances. `src/type-erasure-PROOF.bend` fills all 17 erasure
laws. Its evaluator equations quantify over environments, frames, arguments and
books, with an explicit one-step fuel adjustment. They describe existing erased
machine transitions; they do not prove whole-program source erasure or checker
soundness. The complete frontend proof also fills the restated generic-header
acceptance law. No hole, axiom or unsafe inhabitant discharges these obligations.

The gate reruns the seed and checks every fixture source hash, both evaluator
lanes and actual Wasm execution. Mutants are independently seed-typechecked;
host failures, internal errors, exhaustion and invalid Wasm are not semantic
kills. Literal ABI expectations precede that mutant and inspect exports without
invoking a generic or cell-valued host signature.

The frontend's generic-header pin was superseded under the coordinator's
review-round-1 authorization (phase expectations from the seed reference). The
classify-2 type-application pins and two of its laws conflict the same way; a
proposed supersession awaits authorization. Live semantic and style review
remain coordinator-owned. Offline preflight supplies context coverage and
blockers only; there are no conceptual compression, Delight, memetic identity,
Anticipation or Payoff ratings yet.

The dispatch boundary corpus fixes local type/quantity forms before repairing
their diagnostics. Both checker paths preserve lexical shadowing, recognize a
global datatype only after lexical lookup fails (one shared `scope.bend` rule,
`term_name`), and reject local type-level normalization as Unsupported.
`check-dispatch.bend` chooses the path per book. Empty type-argument lists
are seed-invalid.
