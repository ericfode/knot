# Bounded review of the first source-to-Wasm compiler

Reviewed on 2026-09-26 with Perch 0.3.5 and resolved model **jev-1.13.0**.
[Raw answers and usage](receipts/perch.json) retain 344 checks in 104 requests
and 104 responses across 19 targets: 103 parsed Bend declarations and one law
packet. Every selected target had nonzero coverage and a completed response.
All recorded source/context file hashes match the reviewed working copy.

| Target | Checks / requests |
|---|---:|
| eval.bend | 72 / 18 |
| wasm.bend | 96 / 24 |
| wasm-bytes.bend | 33 / 11 |
| driver.bend | 44 / 11 |
| compile-cli.bend | 27 / 9 |
| eval-cli.bend | 18 / 6 |
| diagnostic.bend::error and ::status | 2 / 2 |
| runtime-LAWS.bend and runtime-PROOF.bend | 28 / 14 |
| Eight new fixture main declarations | 16 / 8 |
| LAW_REVIEW.md, all eight law rules | 8 / 1 |

The implementations were reviewed for checker trust, pattern sharing, fuel and
machine arithmetic; byte composition also received the growing-prefix-copy rule.
The IO entry points received effect-boundary checks and the driver received the
borrow-lifetime rule. Exact selections and below-floor answers are retained.
No source or law implementation produced an above-floor finding.

The fixture review did produce one finding: `bend-machine-arithmetic` assigned
0.81 broken probability to `mixed-types.bend::main` (floor 0.80). **False-positive.**
The complete 15-line fixture contains only nullary enum constructors, one match
and a direct call. There is no arithmetic, conversion, bound, size or index
operation. The independent gate records main = Green/tag 1 and six choose calls,
matching the pinned interpreter, evaluator and actual Wasm on both build lanes.
The raw exit 3 and verdict are preserved; no fixture, oracle, source or rule
threshold changed. No confirmed repair or stronger-model repair task was needed.

Related below-floor arithmetic answers on other constructor-only fixtures
(0.67–0.79) have the same applicability problem. The law packet's essence (0.70)
and composition (0.66) signals do not identify a concrete defect. Its contract
explicitly limits the seven new laws to machine transitions and concrete codec
normalizations. Independent finite whole-program tests supply broader evidence;
there is no universal source-to-Wasm simulation theorem. These are limits to
retain, not missing proof claims to disguise.

Context is bounded: 16 helpers, four callers, 12 files and 48 KB. Twenty-one
declaration contexts are marked truncated; 96 retain unresolved references such
as Base operations, imported type identities or constructors. Each target
declaration is complete. The receipt lists affected units and exact local files;
Perch did not load the seed's full package closure or type-check those contexts.
The separate deterministic proof/build/trust gates cover that work. The syntax
Error datatype addition has no executable declaration itself; error/status and
their actual helper contexts were selected.

The eight fixture checks select main and visible helpers, not every repetitive
declaration in the 130-function boundary fixture. Every fixture is nevertheless
checked and executed by the deterministic gate. Existing frontend/checker paid
reviews were not repeated; their regression gates were rerun after HostFailure
was added. No ranking of complementary evaluator/emitter implementations was
invented. These semantic judgments are advisory, not a correctness proof or a
measurement of model precision.
