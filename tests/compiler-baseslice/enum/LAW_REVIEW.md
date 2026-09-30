# BS1 law and conformance review

Contract: seven pinned enum-source declarations check as an ordinary source book,
and the existing independent evaluator and Wasm emitter preserve their values,
constructor order, quantities and composition. Imported Base, VM images and
whole-Base checking are outside this contract. The complete follow-on plan is
[BASE-SLICE-PLAN.md](../../../docs/compiler-campaign/BASE-SLICE-PLAN.md).

## Coverage and inhabited witnesses

| Declaration / boundary | Independent runtime observation | Source proof / negative |
|---|---|---|
| Bool / Bool.not | `boolean::neg(False/True)`, main and composed | universal `not_involution` |
| Bool.and | all four ordered argument pairs; all eight composed triples | universal `and_associative`, `de_morgan`; affine-reuse, wrong-type, wrong-arity |
| Bool.or | all four ordered pairs and composed triples | universal `or_associative`, `de_morgan`; reusable control consumes two copies |
| Cmp / Cmp.is_eq | `cmp-unit::equal` and rebuild on LT/EQ/GT; ordering(False/True) | three checked ground equations fix EQ=1, LT/GT=0 |
| Unit | `cmp-unit::singleton()` | universal `unit_unique`, witnessed by Unit{} |
| exhaustive Bool matching | both Bool values in positive books | missing-arm seed rejection and exact `Invalid check missing-arm` |
| unsupported import | seed-valid `import-base::main()` returns Yes | both Knot builds refuse all phases, create no artifact and preserve existing bytes |

Boolean domains have two inhabitants, Cmp has three and Unit has one. Quantified
Boolean laws include no precondition or empty type. Three Cmp equations are
ground normalization; the other five laws are universal finite-domain proofs.
`PROOF.bend` uses checked fills, no holes, axioms or unsafe local definitions.
The seed trust audit includes all loaded Base unsafe/foreign declarations,
including ones these source proofs do not execute; it is not a runtime closure.

The fixed expectations came from the seed, before the runner (3b32cc4c). The
reference runs load the hash-pinned, unmodified Base; qualification inputs are
byte-for-byte excerpts and the same consumers. `regen.py` verifies their exact
prefix, frozen file hashes and both oracle lanes on every gate run. The complete
book is checked before evaluation or emission. The emitter is invoked separately
and cannot replace program bodies with evaluator results.

## Adversarial observations

| Mutant | Unchanged witness | Intended semantic rejection |
|---|---|---|
| zero-tags | boolean::neg(False) | validated Wasm returns False/tag 0, wanted True/tag 1 |
| inverted-case | boolean::neg(False) | validated Wasm chooses the wrong Bool row |
| aliased-arguments | boolean::conjunction(True,False) | validated Wasm aliases b to a; wanted False/tag 0 |
| constant-evaluator | boolean::neg(False) | successful, well-formed Bool observation has the wrong tag/constructor |
| lost-type-boundary | wrong-type | mutated checker accepts a seed-rejected Cmp argument to Bool.not |

Every mutant is a one-anchor change to Bend compiler code, type-checked and
built by the pinned seed. A compiler/build/host failure is never a semantic kill.
The runner records source hashes, builds, expected values and actual observations.
Input discard or constant output cannot satisfy the positive truth tables: both
constructors occur in neg/and/or, and all three occur in Cmp rebuild. Composition
and ordered argument pairs catch defects that isolated unary calls would miss.

Remaining attacks belong to later steps: hash bypass, hidden reachable helpers,
name collision/scope mistakes, generic/quantity erasure, field offset/ownership,
IO request dropping and image encoding. No claim of coverage for them is made.
Malformed-source parser errors, byte budgets and deep-recursion exhaustion remain
covered by the unchanged existing gates; BS1 adds no bound or performance promise.

## Reading hypothesis and review disposition

The reading hypothesis is an explicit source algebra, visible through the full
truth tables and a small composition, with laws establishing its symmetries.
Base names and bodies remain exact. There is no score-seeking rewrite.

Conceptual compression, Delight and memetic identity are **unreviewed**: no live
Perch calls were authorized for this implementer. Anticipation, Payoff and
conditional Galaxy brain are also unreviewed. No distributions, ratings or
automatic style pass are claimed. Coordinator semantic/style review remains
required independently of deterministic conformance.

Fresh receipt source identities are in [receipts/enum.json](receipts/enum.json),
including the oracle, compiler, host, trust script and proof-file hashes.
