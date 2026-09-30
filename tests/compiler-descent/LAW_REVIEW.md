# Decreasing-call review boundary

The fixed contract is [SPEC.md](SPEC.md). `src/descent.bend` compares live
parameter columns lexicographically and constructor fields componentwise.
`GT` means equal-or-smaller was not established. Alias provenance serves only
comparison; emitted references and quantity accounting stay separate.

The 23 laws in `src/descent-LAWS.bend` are filled by
`src/descent-PROOF.bend`. General equations cover product identity/growth,
erased columns, empty columns, alias heads, failed-field exclusion and budget
boundaries. Ground witnesses cover variable identity, rebuilt constructors,
subterm fallback, opaque applications and exact transition costs. These are
not a general termination, descent-refinement or compiler-soundness proof.

The original 38 rule/legacy expectations, two resource expectations, 12 boundary
cases and seven type-correct semantic mutants remain unchanged. The refresh
adds a separate immutable seed freeze: 28 new edge programs and six verbatim
nest round-4 sources. Seed book execution and native/Bun generated execution
observe the same outcomes. For seed executable builds only, the wrapper adds
`import Base` before the unchanged fixture body. The gate checks both compiler
lanes through checking, the independent evaluator, actual Wasm execution,
identical emitted module bytes, and preservation of an existing output on
rejected compilation. A host error or timeout cannot satisfy a source pin.

The refresh probes cover a fourth parameter column, erased columns between
equal columns, opaque later arguments after an earlier decrease, nested
rebuilding, three-field product growth and shrink, both subterm-search sides,
alias chains/shadowing, illegal alias scrutinees, affine alias reuse and dead
growing calls. The partial-coverage control removes only the recursive call
from nest's `rebuilt-partial`; the seed then reports `cases for Leaf`, confirming
the branch's earlier `Invalid check missing-arm` diagnosis for that matrix.

## Required open obligations (D21)

| Required statement | Branch evidence | Disposition |
| --- | --- | --- |
| An arbitrary irrefutable first row lowers to its body | Ground `irrefutable_lowering_selects_first`; specialization/default/selection helpers; frozen first-match/wildcard fixtures | Open. The seed-accepted 13-column `matrix-work` control exhausts the implemented work quota. Do not replace the required statement with a successful-lowering-only claim. |
| An arbitrary exhaustive matrix lowers without missing branches | Ground `exhaustive_matrix_has_no_missing_branch`; frozen multi-column/nested/empty-type fixtures | Open. The ground instance is not a general theorem. |

Both remain recorded in `src/SPEC.md`. Nest's later partial-correctness proof
and total-law qualification belong to the coordinator's merge, which must
preserve these obligations and the newer evidence together.

D24 affects VM requests and Default handling. This branch adds no VM or IO
capability. Its constructor-pattern defaults remain checked by the nest gate;
the VM integration owns the request-specific Default rule.

The refresh changes no production Bend declaration or accepted expectation.
Live semantic/style review is coordinator-only. Conceptual compression,
Delight, Memetic identity, Anticipation and Payoff have no new model ratings or
distributions here; offline coverage cannot establish an automatic style pass.
