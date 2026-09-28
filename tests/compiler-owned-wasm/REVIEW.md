# Independent ownership review

Reviewed 2026-09-27 for `wasm-owned`. Scope: quantity/liveness lowering, ordered
arguments and lets, branch cleanup, shared Data opening, release resumption and
failure preservation. No unresolved successful-execution ownership defect was
found in this bounded review. This is not a general correctness proof or a
replacement for the complete campaign gate.

## Independent witnesses

- **Repeated boxed child, real shared opening.** The source now retained as
  [shared-boxed.bend](fixtures/shared-boxed.bend) was literal-reviewed before its
  isolated compiler probe. The seed interpreter, independent Knot evaluator and
  actual owned Wasm all return
  `Result{Leaf{Nine{}},Pair{Leaf{Nine{}},Leaf{Nine{}}}}`. Exactly **3 cells** are
  reachable and live. The single Leaf has **3 incoming edges and count 3**;
  Pair and Result each have count 1. Releasing the result leaves live 0 and
  pending 0. [review-cases.json](review-cases.json) retains this additive
  expectation; the original D7 freeze was unchanged.
- **Duplicate-child overflow.** Retain the returned Pair once: Pair count 2,
  Leaf count 3, with the same Leaf in both Pair slots. Set the RC ceiling to 4.
  `__heap_open(pair)` traps with status 3; a copied before/after comparison
  finds **all linear-memory bytes unchanged**, including both counts. Restore
  the ceiling and retry: Pair count becomes 1 and Leaf count becomes 5.
  Release the two acquired child holders and the enclosing result: live 0,
  pending 0. This distinguishes whole-operation preflight from checking each
  repeated edge only immediately before its increment.
- **Nested alternatives.** A Type Pair holds distinct `Leaf{Off{}}` and
  `Leaf{On{}}` values. Two nested Flag matches select the second reusable
  argument. Seed, evaluator and Wasm agree on `Leaf{On{}}`; exactly 1 cell
  survives, and releasing it leaves live 0. This checks cleanup in alternatives
  and transfer through an affine parent's fields.
- **Complete proof entries.** Fresh pinned-seed runs of `src/heap-PROOF.bend`
  and `src/ownership-PROOF.bend` both print `All terms check.`. These establish
  the stated instruction-list and bounded semantic-model equations. They do
  not prove emitted Wasm refinement for arbitrary graphs.

## Fixed export collision

A legal source function named `__heap_live` originally produced `Built` followed
by an invalid Wasm module: duplicate export names for the source function and
the runtime counter. The source's seed result is `On{}`. The owner added the
reserved-name guard after the independent [boundary freeze](boundaries.json).
A rebuilt current compiler now reports `Unsupported emit owned-export-name`
(exit 3) before emission. Source names beginning `__heap_` are explicitly outside
this debug ABI, including `__heap_memory`.

## Failure boundary

Cleanup resumes **its retained work**, not an interrupted source invocation.
An isolated witness defines Data `Leaf{value: Flag}`, Type `Box{value: Leaf}`,
and `discard(a: Box,b: Box) -> Flag` returning `On{}`. Its main expression is
`discard(Box{Leaf{Off{}}},Box{Leaf{On{}}})`; the seed returns `On{}`.

With debug stack limit 1, the first implicit drop traps with live 4, pending 1.
Raise the limit to 4096 and call `__heap_clean(10000)`: it returns 0 with live 2,
pending 0. The other Box and Leaf were held only by the unwound Wasm frame.
Retrying main returns `On{}` but leaves those 2 cells live. This is retained
failure evidence, **not an accepted whole-source recovery behavior**.
[src/SPEC.md](../../src/SPEC.md) and [CONTRACT.json](../../src/CONTRACT.json)
require retiring an instance after a source trap. Direct share/shared-open
preflight and explicit enqueue/clean have narrower preservation/resumption
contracts. The production stack bound exceeds any chain fitting the fixed heap.

The isolated probe sources and observations are local under
`.local/wasm-owned/review/`; the durable shared-child and export-boundary witnesses
are included in the gate. No source implementation was changed by this reviewer.

## Final argument and tail-call delta

Reviewed the final `owned.argument`, `tail_calls` and `function_body` changes.
Call arguments now remain on the Wasm operand stack in source evaluation order;
constructor arguments still use saved locals for ordered field stores. Each
later argument leaves one result above the earlier holders, and quantity-driven
sharing still occurs before an earlier reference can outlive a later consuming
use. No ownership defect was found in this change.

A fresh isolated source probe calls `pair(x,churn(x))` with reusable `x`, where
`churn` opens and reconstructs its Leaf. Seed, evaluator and owned Wasm agree on
`Pair{Leaf{On{}},Leaf{On{}}}`. The two distinct Leaf cells and Pair are all live
(count 1 each), and releasing the result leaves live 0 and pending 0. This
exercises a holder on the operand stack across a nested call and reallocation.

Tail calls retain `return_call` only when both target live arity and the complete
source local frame are at most 16 slots. The source emitter's conditional
instructions are currently flat lists, so `tail_calls` visits the return-call
instructions inside each source branch. Replacing a tail-position `return_call`
with `call` leaves the result to flow through the enclosing branch/function end;
it introduces no extra ownership action. A later change to structured instruction
containers must preserve this traversal invariant.

An independent 16/17-slot fixture validates and runs under default Node. The
16-parameter caller to a 16-parameter target keeps `return_call`; a 17-parameter
caller to a one-parameter target and a zero-parameter caller to a 17-parameter
target use ordinary `call`, confirmed with `wasm2wat --enable-tail-call`.
All four tested nullary entry exports return ordinal 1 with live 0 and pending 0;
the main result also agrees with seed and evaluator. The complete updated
ownership proof entry prints `All terms check.` (13 ownership laws; the heap mechanism has 30 laws, now split between 17 source equations
and 13 independent test-packet model laws). The [historical Node failure](receipts/attempt-wide-tail.json)
remains HostFailure evidence, not a source rejection or mutant kill. This bounded
fallback has no unresolved finding in this review; wide source calls can exhaust
the host stack.
The source-trap instance-retirement requirement above is unchanged.

## Reviewed source snapshot

Hashes below identify the current sources read for the completed review,
including the repaired export guard. Later edits require separate review.

| Source | SHA-256 |
| --- | --- |
| `src/ownership.bend` | `a8356b542c577cf66e20e329be479c6045785b658257f13c4de4ec83021d694d` |
| `src/owned.bend` | `27c3c35bd5774b581889e13db66730012b8af2b31d2e96bfe1b64df631284244` |
| `src/heap.bend` | `911c3af790397e16f7fb0a951cf73dfa13ab08d50926e693927ffe0c13034361` |
| `src/heap-code.bend` | `b992a6a3c0c953670695bc937e4ab40f30d915eb1829d30b05dfae276c38ac40` |
| `src/ownership-LAWS.bend` | `7ad7faa8fabe532c6b659ae4bf1622fd01782a71fd192e64f55a610cc2bb174a` |
| `src/ownership-PROOF.bend` | `665337166e5999a82f93c7b91bc20f87f111317b6c419670657980c775f6bd4f` |
| `src/heap-LAWS.bend` | `0043d1f7351190bcf5b78314f058ae07029fe97f6c184e2a24b06f841884c4bb` |
| `src/heap-PROOF.bend` | `f8d8af62ee007cf38055c2145544d40c322841d089091632bd2e99ba8cb3b803` |

## Source/test proof boundary

The unchanged manifest control requires source groups to close over local imports
without including test/research files. After the review above, the owner moved
the 13 independent semantic model laws and their proof entry from the source
heap packet into `model-LAWS.bend` / `model-PROOF.bend` here. The equations and
proof bodies are unchanged; the 17 concrete heap equations remain in `src/`.
Both complete split entries print `All terms check.`. The gate requires these
two entries and the 13-law ownership entry, retaining all 43 laws. Runtime and
ownership lowering are unchanged. The source snapshot table above reflects
this placement change; the model packet hashes are:

- `model-LAWS.bend`: `c790115cc012a9203db5d9aec6a75dec8e9815f887b488d778a0ae7ae05ffc2a`.
- `model-PROOF.bend`: `48c107ab4e880756e21664b29cf66e7e23db7032ee1c2b900be3cbf5517ec733`.
