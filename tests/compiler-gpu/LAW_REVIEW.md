# Records lowering — bounded law review

Contract: `SPEC.md`; implementation: `src/records.bend`; complete proof entry:
`src/records-PROOF.bend`. This packet describes lowering from an already checked
Book, not a checker, scheduler or general compiler-correctness theorem.

The central invariant is one statically named capture per binding owner inside a
reserved activation interval. Source quantities decide whether an occurrence
moves that owner or acquires a reusable Data edge. Temporary argument ranges
and result captures are distinct. Case opens the selected constructor; scope
exit releases remaining bindings. The independent runtime2 reference audits
all physical owners after every instruction. The source gate additionally
requires exactly one nullary result object/root, no pending cleanup, and no
unconsumed join at halt.

| Public observation / operation | Evidence |
|---|---|
| `emit`: checked source to a valid version-2 bundle | 53 fixed seed calls over 9 programs; native/Bun byte equality; independent evaluator and actual Wasm agreement; existing bundle validator |
| `transfer`, `bind_slot`: affine move and reusable Data acquire | `affine_occurrence_transfers_an_edge`, `reusable_occurrence_acquires_an_edge`, `affine_binding_moves_even_data`; sharing fixture and RC-limit-one affine control |
| `release`, `returned`: cleanup before result delivery | `dropped_binding_enters_cleanup`, `return_cleans_before_delivery`; discarded Type trees, unused fields, final owning-state assertion |
| `deliveries`: logical argument order | `completion_carries_issued_attempt`, `logical_slots_survive_reverse_delivery`, `erased_argument_has_no_slot`; asymmetric first/second and reverse delivery |
| `bind_parameters`: erased slots | `erased_parameter_has_no_owner`; erased fields, erased forward call and constructor ghost controls |
| Tail self-call parameter transfer | `tail_arguments_keep_source_order`; parity on 0/1/2/5/6 successors, a unique Type chain with a changing accumulator, executed back edges |
| `relocate`: preserve tests and fix only code operands | `relocation_preserves_the_test`; all emitted bundles validate; three-color branch differential |
| Capture and compilation boundaries | `full_activation_cannot_wrap`, `pending_compilation_needs_fuel`; zero/exact/one-past output budgets, depth exhaustion |
| Rejection classification / publication | Three seed-accepted unsupported programs, both builds, absent and existing output; invalid source, entry/domain errors; no Built record or changed output |
| Host / runtime | Explicit Invalid, Unsupported, Exhausted, HostFailure and InternalFailure paths; zero quantum; capacity limits; full CPU observations; device comparison command |

The thirteen laws are universally quantified normalization proofs of specific
helpers and control boundaries. Their types are inhabited by ordinary U32,
Bool, token, catalog, scope and plan values. They do not assert that arbitrary
invented Plans or unchecked Books are valid. The runtime gate supplies concrete
well-formed witnesses and independent semantic checks of the composition.
There are no holes, new axioms or user unsafe definitions. Existing Base and
byte/IO helpers remain seed dependencies, with the campaign's existing trust
boundary; this is not a self-hosting claim.

Five compiler mutants must typecheck and emit validator-accepted bundles before
execution can kill them. A wrong branch tag and swapped logical argument slot
return the wrong literal tag. Move instead of reusable Data share and stale
attempt delivery produce runtime Invalid. Replacing release with a yield keeps
the correct result but leaves additional owners. The last assertion is necessary:
checking only the returned tag would admit a leaking compiler.

A manual hostile reading also found that the first draft chose transfer solely
from the datatype kind. That would add an unnecessary RC edge for an affine Data
binding and could exhaust a count limit of one. The final code uses the checked
quantity as well; a filled binding law and the independent count-one runtime
control cover the distinction. No fixed source expectation was changed.

The source corpus does not establish general recursive allocation, dynamic
attempt transport, cancellation, concurrency, resource adequacy for arbitrary
programs, general Wasm recursion support or a WGSL refinement theorem. Immediate
attempt operands are sufficient only because every emitted join starts once.
Calls inside recursive bodies are conservatively Unsupported, including a
nonrecursive helper in a base arm. Bounded tail self-calls allocate neither a
join nor an activation on the back edge.

Offline preflight is recorded separately and is not an advisory style pass.
All five style axes (Compression, Delight, memetic identity, Anticipation,
Payoff) remain unrated. The coordinator must review the omitted helper/import
contexts, run live semantic/style checks, and run the identical generated bundles
on Metal before promoting GPU execution. Receipt input hashes identify the
exact checked source; `receipts/gpu.json` and `receipts/observations.json.gz`
contain the deterministic compiler evidence.
