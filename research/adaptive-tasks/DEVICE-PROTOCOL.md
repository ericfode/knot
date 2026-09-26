# Device layout and phase contract

Scope: the exact `tasks.wgsl`/`check.mjs` pair in the recorded receipt. This is a
bounded implementation argument plus device tests, not a mechanized memory
model proof. All fields are U32 words, little-endian on the tested arm64 host.

## Records

| Record | Words, in storage order | Size |
|---|---|---|
| Op | kind, left, right, seed, ticks, factor, bias, parent, slot, pad0, pad1, pad2 | 48 bytes |
| Task | state, remaining, value, left_value, right_value, mask, last_worker, moves, runs, steps, destination, slot, factor, bias, completed_round, pad | 64 bytes |
| Params | count, quantum, capacity, root, round, reverse, adaptive, pad | 32 bytes |
| Control | atomic count, atomic error, pad0, pad1 | 16 bytes |

Op kinds are Leaf=0, Fork=1, Then=2. `0xffffffff` means no parent/child/previous
worker/completion round where applicable; node IDs cannot reach that sentinel.
Task states are Dormant=0, Enter=1, Run=2, Waiting=3, Frame=4, Done=5,
Retired=6. Left is logical slot 0; right is slot 1. `destination` records the
parent ID and survives all state changes. The root's destination is the sentinel.

The host accepts only recursively validated trees, at most 4,096 nodes and
depth 64, with at most 4,096 ticks per leaf. Postorder packing makes children
precede their parent, assigns each child exactly one parent, and forbids cycles
by construction. It is not a decoder for arbitrary graph records. Quantum is
0–64; round budget is 1–512; capacity is 0–node count. These bounds keep offsets,
reservation counts, and instrumentation counters within U32 and buffer limits
on the tested adapter. General size/offset algorithms remain separate work.

## One round

```mermaid
flowchart LR
  A[Immutable previous state] --> P[Prepare: activate and gather]
  P --> X[Execute: bounded work per ready task]
  X --> J[Join: capture ordered results and retire children]
  J --> B[Next state and host outcome]
  B --> A
```

**Prepare.** Each invocation copies one previous record to its own work slot.
A dormant child becomes Enter only after its parent was Waiting in the prior
round. Runnable slots reserve distinct frontier positions with atomicAdd.
The reservation count is bounded by node count, so cannot wrap. A reservation
outside capacity sets an error and writes no frontier element. A later execute
dispatch reads the fully published records/frontier; the counter alone is not
used as same-dispatch publication of ordinary payload writes.

**Execute.** Adaptive mode maps a lane through the frontier; fixed mode maps it
directly to a task ID. Unique IDs give one writer per work record. Each task
runs at most its quantum: Enter initializes a leaf or suspends a parent for its
children; Run advances ticks or completes; Frame consumes saved ordered child
values and unary captures. Remaining work stays in the record. No invocation
waits for another workgroup. An exhausted frontier skips this phase globally.

**Join.** Each invocation reads the now-immutable work snapshot and writes only
its own next-state record. A Waiting parent captures each Done child into its
logical slot exactly once, using a mask, then becomes Frame when ready. A Done
child uses the same snapshot to determine whether that parent accepts it and
becomes Retired, clearing its value. The phase boundary establishes the new
logical ownership: parent captured value, child invalidated. Old snapshot bytes
still exist but cannot authorize task execution; buffers are not reused for a
new logical object within the run. The unique-parent tree premise is essential.

Work and next are distinct buffers. Successive rounds swap the two state
buffers, after ordered dispatches and host readback. No invocation reads another
invocation's writes within the same dispatch. The host destroys a run's buffers
only after `onSubmittedWorkDone`; there is no cancellation/reuse protocol here.

## Observations and limits

Host checks preserve every task's destination/slot on every round. All frontier
words at and beyond capacity must retain their initialization canary, including
capacity 0 and 1 cases. Finished root values must match the Bend oracle and all
non-root tasks must be Retired. Early exhaustion produces an explicit resource
outcome; it is fail-stop for this harness, with no resumable allocator claim.

The device has an administrative Enter step absent from Bend's `Task.start`;
CPU and GPU budgets are not asserted to count identical transitions. The CPU
fuel law is universal over its own machine. Device checks compare source
results and explicit bounds over finite fixtures. A universal simulation,
arbitrary histories, generic affine environments, shared Data, dynamic forks,
and generation-checked slot reuse remain open.
