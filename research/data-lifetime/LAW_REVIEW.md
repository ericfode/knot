# Data lifetime law review

Contract: [SPEC.md](SPEC.md). Public model entry:
`transition(Command, Store) -> Store & U32`; Store is affine, Heap is immutable
graph metadata. Status 0/1/2/3 means Ok/Invalid runtime request/Unsupported/
Exhausted; missing internal records use 5 (InternalFailure). Failures preserve
the input state. Cleanup exhaustion returns its partially progressed state and
retained obligations. Host failures and timeouts are separate harness outcomes.

The core invariant is an incoming-obligation equation: roots + live object edges
+ pending cleanup references = each record's count. Type counts are exactly
one. A counts are all one. Data points only to Data; each child predates its
immutable parent. Reader leases authorize observation but are not ownership
edges; they block physical reuse globally. Logical release moves its obligation
into pending work. Opening a shared B parent creates child holders while keeping
its remaining parent edge obligations balanced.

The independent Python oracle uses dictionaries, recursive copying and in-place
count updates guarded by whole-operation snapshots. Bend uses list metadata,
an explicit copy-frame machine and persistent failure results. The comparison
retains every cell field, identity/count, root, lease, pending obligation, Type
serial and metric after each operation. There is no opaque contents-only checksum.
Cross-policy comparison forgets identities/counts but compares complete ordered
root/reader values until a deliberate capacity/count divergence.

| Public operation | Filled equations | Independent witnesses and mutants |
| --- | --- | --- |
| alloc | copied_allocation_installs_owner, counted_allocation_starts_at_one, empty_capacity_rejects_allocation | Leaf/branch Type and Data, zero/exact capacity, preserved child owner on full; failure-owner mutant |
| share/dup | copied_leaf_has_distinct_owner, counted_leaf_retains_one_record, type_is_not_shareable, count_ceiling_preserves_state | Recursive trees/lists/DAGs; rollback after partial copy; alias-original, reversed-fields, missing-retain, count-ceiling, Type-copy mutants |
| take/consume | consume_transfers_fields, shared_open_acquires_children | Mixed Type/Data reconstruction, shared parent and repeated child edges, count overflow partway through open; retained-parent and missing-child-acquire mutants |
| release/cleanup | release_queues_without_disposal, type_last_release_drops_once, copied_release_keeps_other_value, data_first_release_keeps_alias, data_last_release_reclaims, zero_budget_retains_obligation | Budgets 0/1/large, unrelated and repeated edges; free-first, never-free, duplicate-Type-drop, lost-tail and lost-zero-budget-work mutants |
| move/suspend | suspension_moves_one_holder | Ready/frame/join holder transfers, occupied/duplicate/late slot rejection, resume/cancel paths; suspended-root, partial-join-root and failure-owner mutants |
| reader pin/ack | reader_blocks_reuse | Two readers, first ack insufficient, take blocked, final ack permits complete cleanup; early-reuse mutant |
| failure/cycle | rejected_transaction_preserves_state, successful_transaction_publishes_state, immutable_graph_rejects_backpatch | All statuses, transaction rollback and graph birth-order checks; unchanged input-owner observations |

**Proof boundary.** All 20 declarations are `law` declarations with filled
`{==}` proof definitions, checked together through `PROOF.bend`. **19 equations
have binders, one is a concrete normalization**. Binder presence does not make the fixed-shape heap
equations arbitrary-graph theorems. The transaction laws quantify arbitrary
snapshots; allocation/share/drop laws mostly normalize inhabited one/two-record
states with arbitrary scalar contents. None proves universal graph refinement,
acyclicity, arbitrary repeated release, allocator correctness or concurrency.

Every heap witness is inhabited by explicit records and holders. The laws include
nonempty successful values and surviving aliases, not just empty-store failure.
There are no new axioms, holes, `@unsafe` definitions or foreign store operations.
The seed's entire Base still contributes 42 foreign declarations and the existing
two unsafe array primitives to its checked closure; generated model execution
uses only `IO.print`. Arithmetic lowering, host allocation and seed GC are trusted.
The affine wrapper does not prevent forgery through its public snapshot metadata;
this is a model, not a general-purpose owning heap.

Hostile reread tested the following alternatives: an always-retain collector,
early reclamation with a surviving alias/reader, forgetting a work item at zero
fuel, sharing raw owner bits, dropping a Type serial twice, preserving a failure
status while losing an incoming owner, and reversing clone fields. All are
type-correct executable mutants; all fail frozen public observations. The initial
double-drop mutation reused an affine scalar binder and failed quantity checking;
it was **not** counted as a kill. The retained mutant appends a second literal
serial 7, remains type-correct, and fails the serial-7 witness for the intended
reason. This changes no expectation or accepted implementation.

The oracle checks incoming counts, kind/edge compatibility, acyclic birth order,
reader survival, committed live-word accounting and allocation/free conservation
after every step. Final generated workloads require complete reclamation, and
four literal source results are checked against the seed interpreter and Knot
evaluator. The missing fielded Wasm lane is explicitly Unsupported. Two program
families share a traversal API inside Bend; the independent Python and literal
controls address correlated policy bugs but do not prove completeness.

Remaining adversarial obligations: bounded metadata/worklist allocation failure,
abort/retry of a partially executed device copy, disposer closure captures,
generation/arena transport, unknown graph input, cancellation attempt IDs, GPU
publication races and integer overflow on traces outside the stated bounds.
The model's global reader barrier intentionally trades progress for a simple
sequential lifetime contract; it cannot serve as evidence of a concurrent RC
algorithm. Generic Type payload ownership remains the separate owned-store gate.

Hashes, concrete failing observations and complete proof/trust commands are in
`receipts/gate.json` and `receipts/trust.json`. Offline preflight has 15 truncated
declaration contexts; semantic/style review by Perch remains unrun here under
the executor's no-network boundary. This packet makes no live-review pass claim.
