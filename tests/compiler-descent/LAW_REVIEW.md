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
## Executor precheck repairs (2026-09-29)

`precheck-SPEC.md` restates the fixed C1/C3 task. Commit `9b33f2cb` independently
freezes the nine exact reported source hashes and 14 adjacent controls in the
pinned seed's parse, book, native and Bun lanes: 15 accepted and eight rejected.
No earlier expectation, law or mutant changes in this repair.

`check-prechecks.py` passes 23 fixtures / 184 phase observations, 11 accepted
books / 22 evaluator values / 22 actual Wasm values, 11 equal module pairs and
24 preserved refusal artifacts. Seven type-correct semantic mutants are killed
in both lanes (14 kills). They restore each observed failure: wildcard as value,
empty-column false Invalid, residual alias duplication, detached pattern brace,
dotted local binding, missing declaration-event validation, and lost source
position. The unlocated deep match now reports the function boundary
`Exhausted check budget 73:74:7:4` in all three downstream phases.

`precheck-LAWS.bend` has eight filled laws in `precheck-PROOF.bend`. Wildcard lookup
and empty-variable refusal quantify over their helper inputs; the other six are
ground equations for the usage algebra, lexical shadowing, pattern events and
source location. No general parser/checker soundness, residual-region lowering
or matrix law is claimed. The required general matrix laws above remain open
under D21. The residual guard is conservative; Default-core integration remains
required for complete support.

The bounded offline style preflight prepares all 54 changed/new declarations in
nine files with zero provider calls. Its fixed task is available (2,208 bytes).
Six contexts truncate, and the composition exceeds 48 KB with one unavailable
collaborator. Conceptual compression, Delight, Memetic identity, Anticipation and
Payoff have no live scores or distributions. Each axis is unavailable against its
applicable target; no automatic style pass is claimed. The initial broader
preflight's 165 units / 24 truncations and oversize task remain in ignored evidence.

The shared runner now differs from its effective base only by additive gate/count
rows, and its required-name test only by added names. Five affected legacy gate
drivers are byte-identical to the effective base; seven timeout changes were
removed in total. The earlier classification and
recursion assertion/mutant migrations retain their independent freezes and
original witnesses; the coordinator must reconcile those D26 changes at merge.
The full registered suite and committed-head precheck replay are pending at this
implementation checkpoint. The complete results belong in the repair report.

The first full-suite run caught an overbroad residual refusal before the existing
`nested-alias-affine` control could report its concrete quantity failure. The
checker now retains `Invalid check affine-reuse` and applies the conservative
guard to the remaining results. Both lanes preserve that immutable diagnostic
and refuse default alias duplication/rematching. The source-manifest completeness
assertion also caught four omitted files; three new groups and the required local
import closures restore coverage without changing any test.

Nest's frozen affine mutant then exposed duplicate quantity enforcement: the
independent residual guard masked the mutation of `E.sequential`. Each counted
residual occurrence now contributes the same level to the canonical scope merge;
its conflict is classified through the existing residual refusal. Inspection
remains an independent capability boundary. The quantity primitive, mutant and
original witness are unchanged. Normal controls and both frozen affine mutations
are replayed before the serial full-suite qualification.

The guard is admission-only and now returns `Unit` instead of carrying the
unchanged scope through its result. The scope extension remains `M.alias`'s
operation. Both lanes replay the normal controls and both fixed affine mutants
with unchanged outcomes (10 observations); the eight-law proof still checks.
Direct native builds retain the default O3 flag. No build-time speedup or causal
effect is claimed from these observations; the final full-suite result decides
qualification against the unchanged host deadlines.
