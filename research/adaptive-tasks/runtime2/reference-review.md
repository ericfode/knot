# Independent host reference

`reference.py` was implemented from `SPEC.md`, `layout.json`, `fixtures.json`
and the literal/formula controls in `boundaries.py`. Its author did not inspect
the Bend model or WGSL interpreter implementation. Python objects represent
the owning graph; the reference does not decode device words or share a
transition implementation with either execution lane.

`Reference(config).step(command)` accepts a command with at most eight u32
words, zero-pads it, and returns a detached complete observation. Configuration
must first pass the separate bundle/layout validator. `instructionCount`
defaults to `4294967295` for isolated models; the harness supplies the actual
instruction count. Code identities are instruction indexes. The reference
does not certify storage binding sizes, version/profile negotiation or device
execution.

After each command, the reference recounts owners from captures, pending
releases, object child edges and join results. Saved capture ranges designate
the existing capture slots and do not add another edge. The independent audit
requires:

- Every owning edge points to a live object; every live object is reachable.
- Data RC equals its incoming edge count. Type has exactly one owner.
- Data children are Data, and all child identities precede their parent.
- Live identities are distinct and already issued; `freed + live = issued`.
- Every capacity, object arity, join shape and join state remains consistent.
- Active joins' saved capture ranges are disjoint; ordered result occupancy
  equals `received` until resume or cancellation.
- Cumulative completion count is bounded by accepted attempt count.
- Rejected operations preserve the complete owning state. Cleanup alone may
  commit a prefix before exhausting, retaining the remaining pending stack.

Shared open checks the aggregate acquisitions for repeated child identities
before any mutation. Cleanup pushes children in declaration order and pops from
the end. Cancellation pushes saved captures in ascending slot order, then
ordered results. Resume keeps the saved captures and cumulative completion
counter. A zero-arity start completes immediately. Reader leases block open and
cleanup; `clean` reports Exhausted even when the pending stack is empty.

The literal `type-not-shareable` control classifies an attempted Type retain as
Unsupported. A Data object containing Type, a stale attempt, occupied/empty
capture misuse and wrong open arity are Invalid. Runtime resource limits are
Exhausted. Oracle invariant violations raise `AssertionError`; they are never
converted into successful observations or ordinary semantic rejection.
