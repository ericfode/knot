# TermStore specification

The supported API is INTERFACE.md. All implementation and oracle semantics are
Bend. The package supplies first-order Data storage and explicit memo cells; it
does not define Knot's AST, evaluator, continuations, or runtime scheduler.

## Abstract state and identity

A realm owns one affine `Scopes(next,available)` chain. Creating a store consumes
one fresh scope. The final scope 4294967295 is usable once, then creation fails
ScopeExhausted forever. `Scopes.from(n)` begins an explicitly supplied range;
independent roots must not be mixed. This is a caller namespace discipline, not
hidden pointer identity, a global allocator, an unforgeable capability, or a
process-wide uniqueness guarantee. IDs are `Id(scope,slot)` with both fields U32.

An arena denotes `(scope, bound, [v0,...,v(n-1)])`. Its logical bound is the smaller
of the requested U32 limit and Vec.maximum() = 16,777,216. Zero is valid. Store
creation consumes a scope even when its bound is zero. Allocation when n < bound
appends the exact payload and returns Id(scope,n). All earlier IDs still designate
their original positions. At bound, allocation fails Limit without changing the
arena. Slots are never removed, recycled, or renumbered. No overflow-producing
increment is reached: n < bound <= 2^24 before append, and the scope allocator
checks its final value before incrementing it.

Get and set compare scope first. A mismatch is WrongScope even if the slot is also
out of bounds. With matching scope, slot >= n is Bounds. Get returns the exact
value at a valid slot. Set changes precisely that slot and returns Unit; all other
cells, n, scope, and bound stay fixed. Failed operations preserve every observation.
Snapshot returns all values in slot order. Length and limit are exact metadata.

State is affine Type. Operations consume the old owner and return the new owner
beside a result, including failures. There is no persistent old-store snapshot
unless the caller explicitly copies Data observations. Dropping an owner ends its
lifetime; IDs do not extend it. Other stores from the same Scopes chain reject
old IDs. The caller must quiesce device/continuation users before freeing the
whole store. Bend module helpers and container constructors are technically visible;
directly fabricating containers, extracting Memo's Store, and altering Vec internals
are outside this API contract. Plain IDs may be reconstructed from numbers.

## Memo state machine

An unallocated ID is absent (Bounds or WrongScope), distinct from a Pending cell.
Each allocation appends Pending. The table fully specifies Cell.step/Memo.apply:

| Before | Begin | Succeed(v) | Reject(e) | Cancel |
| --- | --- | --- | --- | --- |
| Pending | Evaluating, success | unchanged, InvalidTransition | unchanged, InvalidTransition | unchanged, InvalidTransition |
| Evaluating | unchanged, InvalidTransition | Ready(v), success | Failed(e), success | Pending, success |
| Ready(x) | unchanged, InvalidTransition | unchanged, InvalidTransition | unchanged, InvalidTransition | unchanged, InvalidTransition |
| Failed(f) | unchanged, InvalidTransition | unchanged, InvalidTransition | unchanged, InvalidTransition | unchanged, InvalidTransition |

The named begin/succeed/fail/cancel operations are exactly these actions. Each
accepted transition affects only its addressed cell. Ready and Failed are terminal.
`inspect` returns the actual state. `result` gives Done(Done(v)) for Ready(v),
Done(Fail(e)) for Failed(e), and Fail(NotReady) for Pending or Evaluating. Invalid
IDs return the corresponding lookup error. Errors carry no default value.

Cancel is the path for fuel exhaustion/interruption when no definitive outcome was
obtained; it leaves the cell Pending. A caller may alternatively retain Evaluating
and resume its own work. Neither is a completed result. Only finished computations
may call succeed; only definitive domain failures may call fail. This package
cannot verify that a supplied value was computed correctly. There is one serial
owner and no attempt-generation token: cancelled asynchronous attempts must be
quiesced/discarded before retry. Safe concurrent/join protocols are separate work.

## Abstraction and costs

The independent model uses an immutable list and unary Nat indices/bounds. The
abstraction relation is equality of scope, effective bound, ordered snapshot and
length. It does not inspect Vec.Buffer, reuse Array indexing, or call Store/Cell
operations. Memo's model is an action-driven transition table. The implementation
is state-driven; runtime checks compare results and every unrelated cell after
commands. Sharing Base arithmetic and public error/ID constructors is intentional.

On the pinned native/JS array lowering: metadata/get/set and memo transitions take
O(1) slot operations; append is amortized O(1) with O(n) worst-case growth; snapshots
are O(n). Storage is O(n+1), with geometric capacity, excluding retained payload
subgraphs. Dropping/copying payloads and host OOM are additional runtime costs. The
logical resource limit is typed; physical allocation failure is a host failure.
Proof normalization runs structural Base definitions and has a different cost model.

## Evidence boundary

LAWS/PROOF contain a universal generic transition-table refinement theorem, exact
terminal/incomplete result theorems, a universal model append/get theorem, and a
public three-cell growth/write theorem quantified over arbitrary Data payloads.
The latter fixes the operation schedule and arena size. Other equations are
explicit concrete normalizations. No all-length/all-history Vec-store refinement
or universal runtime/compiler soundness theorem is claimed.

Runtime conformance includes fixed boundary/composition witnesses, all 16 memo
state/action pairs, 128 seeded mixed histories of 128 operations, and review
regressions for zero-limit scope consumption and memo growth after completion.
Semantic mutants must type-check before an unchanged named runtime assertion fails.
Scaling is measured separately, with per-ID/per-value equivalence, not an inferred
proof from elapsed time. CPU and JS are the tested targets; GPU is unvalidated.

Trust: pinned Bend parser/checker/normalizer and compiler, unmodified Base (including
its native declarations), Vec's checked interface, native C/JS runtime and toolchains.
Base includes unsafe Array.fork/join declarations; neither is used by this package.
No package law introduces an axiom, TODO, unsafe proof, foreign effect, or new
primitive. Test IO prints/exit are outside the pure core. MIT-0 covers original code;
Base/Vec are dependencies with their own preserved licenses.
