# Generic checking and erasure review

## Review-r0 repairs

The independently reported unannotated matched-parent alias is seed-rejected.
At the public expression boundary, `generics.variable` refuses a refined
binding without an expected type; recursive field reconstruction retains its
existing occurrence path. `generics-LAWS.bend` states three universal equations
for this refusal, unrefined inference and annotated occurrences, all filled in
`generics-PROOF.bend`. The boxed parent and nullary enum witnesses are paired
with annotated-parent, ordinary-alias and pattern-field controls. The
`matched-parent-inferred` mutant restores the original acceptance in both
representations. This is boundary proof and differential evidence, not general
checker soundness. The pure monomorphic checker analogue remains coordinator-owned.

The eleven seed-valid header layouts, including two inherited ones, are
additively frozen before repair. Both parameter routes retain source-adjacency
checks before header layout is consumed. Two separately frozen newline-closer
negatives, a nominal-type parse control and three restoration mutants cover
named/structured parameter routes and newline tokens that must not glue.
Four new filled layout laws cover parameter starts/tails, declaration names
and a named-type closer refusal. Existing colon/arrow laws and all original
mutants remain required. No original law is restated or weakened; the D21
general obligations below remain open. `REVIEW-R1.md` records verification and
the explicit review disposition.

The fixed task is the seed-derived generic/quantity corpus in `expectations.json`
plus the two supplements committed before implementation. Accept generic headers,
instantiate parameter domains and results, check erased arguments, preserve
quantity restrictions, and use one boxed representation for generic families.
The boundary corpus records seed observations for adjacent syntax and kind cases.
No original fixture or pinned outcome changes. At `f39ba7e` the only change
to an existing gate assertion was the restated `generic_header` law. Later
rounds changed others; each is listed with its authorization in
[ASSERTION-CHANGES.md](ASSERTION-CHANGES.md).

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
| A type name that names a definition is Unsupported, in any declaration order | `type_level_definition` (the definition scope below type variables) | Eight seed-valid type-level-names fixtures; type-level-definition-unknown mutant |
| A marked bare binder is a parameter missing its type | `marked_binder` | Six seed-rejected marked-binders fixtures and three agreeing twins; marked-binder-quantity mutant |
| A constructor pattern sees only the datatypes above it | `pattern_order` over the shared `visible` predicate | Four seed-rejected pattern-order fixtures and one local-scrutinee control and three agreeing controls; pattern-order-forward mutant |
| A gap inside a token the seed lexes as glued is Unsupported | `spaced_quantity`; the type parser's `glued`, `flush` and `apart` for `&2`, `<&>` and a closing `>` | Ten seed-rejected spacing fixtures, four seed-valid single-argument closings pinned Unsupported, four agreeing controls; quantity-gap-glued, meet-gap-glued and close-gap-glued mutants |

`src/types-PROOF.bend` fills all 12 algebra laws. The substitution proof is an
induction over expressions with a separate lookup/composition lemma; it is not
limited to fixture instances. `src/type-erasure-PROOF.bend` fills 18 erasure laws. The three catalog
boundary laws and three type-parsing laws have separate complete proof entries;
their six statements and proofs moved verbatim (D21). Its evaluator equations quantify over environments, frames, arguments and
books, with an explicit one-step fuel adjustment. They describe existing erased
machine transitions; they do not prove whole-program source erasure or checker
soundness. The complete frontend proof also fills the restated generic-header
acceptance law. Its parameter type and closing `>` now carry touching spans,
as the lexer emits them from `Type>`: with one shared position for every token,
the adjacency test does not reduce. No hole, axiom or unsafe inhabitant
discharges these obligations.

The gate reruns the seed and checks every fixture source hash, both evaluator
lanes and actual Wasm execution. Mutants are independently seed-typechecked;
host failures, internal errors, exhaustion and invalid Wasm are not semantic
kills. Literal ABI expectations precede that mutant and inspect exports without
invoking a generic or cell-valued host signature.

The frontend's generic-header pin was superseded under the coordinator's
review-round-1 authorization (phase expectations from the seed reference). The
classify-2 type-application pins and two of its laws were superseded the same
way under the later authorization (`78c4942`). Live semantic and style review
remain coordinator-owned. Offline preflight supplies context coverage and
blockers only; there are no conceptual compression, Delight, memetic identity,
Anticipation or Payoff ratings yet.

The dispatch boundary corpus fixes local type/quantity forms and their
diagnostics. It was committed with those repairs in `f39ba7e`, and its Knot
pins await review ([BOUNDARY-PINS.md](BOUNDARY-PINS.md)). Both checker
paths preserve lexical shadowing, recognize a global datatype only after
lexical lookup fails (one shared `scope.bend` rule,
`term_name`), and reject local type-level normalization as Unsupported.
`check-dispatch.bend` chooses the path per book. Empty type-argument lists
are seed-invalid.

Review-round-5 rulings, boundary dispositions and the binding-control count are
in [RULINGS.md](RULINGS.md). `spaced_term_token` proves the shared term-token
refusal; nine newly frozen spacing fixtures preserve declaration-brace controls.
`abstract_identity` reserves an abstract runtime-signature marker, with four
literal evaluator host refusals and unchanged closed seed calls. General parser
soundness and generic application acceptance remain open proof obligations.

Round 6 adds an explicit parse-observation constructor set, with
`parse-order.bend::{known,constructors,run,validate}`. The registered and unseen
pattern guard laws quantify over the visible set, token, arguments and remaining
fuel; the zero-budget law covers refusal. Declared Box and the two late-pattern
fixtures inhabit the guard partitions. The complete proof entry has no holes.
The AST traversal's general correspondence with seed declaration events remains
an open proof obligation; the boundary laws and frozen CLI witnesses are finite
evidence, not its discharge. Five new mutants restore the false-Invalid layout,
false-Unsupported malformed tokens and unsound parse observation. Exact source
identities, unchanged pins and dispositions are in [PRECHECKS.md](PRECHECKS.md)
and the generics receipt's `prechecks` section. The parse CLI guard does not
repair the inherited monomorphic checker residual. Visibility uses original
source offsets; the existing reverse-sequence mutant must still reach its
unchanged Parsed observation. The additional unordered-event mutant attacks
that offset comparison directly.

## Header layout — precheck round 7

`parse.bend::run` normalizes existing line tokens at three header boundaries:
the result arrow after parameters, the monomorphic kind colon and the generic
kind colon. It still expects the delimiter and applies the shared adjacency
guard to the arrow. This uses the existing layout primitive without adding a
frontend helper or changing the depth obligation.

`parse-layout-LAWS.bend` states three boundary equations, filled by
`parse-layout-PROOF.bend`. The generic-colon proof partitions the remaining
token list into empty, singleton and longer tails; it retains its full stated
domain. These are universal boundary equations, not a seed-parser refinement
theorem. The existing D21 parser obligations remain required.

The independently frozen reported probes include both accepted headers and
missing-colon twins. Three new type-correct mutants restore the Invalid
demotions, with the generic-kind and applied-result variants as additional
witnesses. The List control checks the seed's raw empty constructor as well as
its sugared display; boxed Wasm validation is not enum-value agreement.
`prechecks/REPORTED.md` records the fixed reading contract and evidence limits.
Live semantic and all five style axes remain unreviewed by user instruction.
