# Bounded device runtime qualification

Contract fixed before implementation, 2026-09-27. Expected observations in
`fixtures.json` are literal review controls. The independent CPU models are
Bend; Python and JavaScript only serialize fixtures, build, dispatch and compare.
This is handwritten device qualification, not compiler-generated GPU execution.

## R4: slot identity

Use the existing independent `research/owned-store/model.bend` contract for
explicit insert, allocation, take and drop. A locator is `(arena, slot,
generation)`, not authority to extract twice. Every command observes the full
logical store and its reply; failed insertion returns the incoming payload.
Capacity is 0, 1 or 2. Generation ceilings 0 and 1 force retirement. An exhausted
generation retires the slot permanently. Check realm and bounds before reading
payload, then allocation state and generation. Stale, foreign and out-of-range
locators leave the new occupant and unrelated slots unchanged. Free-list order
is observable and agrees with the existing model. All unused words are canaries.

## R6: frontier ownership

Two scalar task records have distinct identities, payloads, destinations and
logical join slots. State encodes the only execution authority: Ready=1,
Queued=2, Running=3, Suspended=4, Waiting=5, Done=6. A task is in the frontier
exactly when Queued (or Running during prepare). A copied ID grants no second
execution: offering Queued, Waiting or Done returns a state rejection.

`Offer(id)` transfers Ready/Suspended to Queued and appends its ID. Full queues
return Exhausted with the rejected task ID and preserve the queue and every
record. `Wake(id)` moves Waiting to Ready; other states reject unchanged.
`Round(quantum, reverse)` accepts quantum 0 or 1. Prepare compacts the published
frontier (optionally reversing physical positions) and changes Queued to Running.
Execute reads only that immutable publication. Quantum 0 suspends unchanged PC;
quantum 1 executes Yield, Wait or Return and advances PC once. Publish empties
the frontier and commits the new states. Yield suspends, Wait waits for explicit
wake, Return completes with the retained scalar payload. Destinations, logical
slots, payloads and instruction ranges survive every phase. No phase reads
another invocation's writes in the same dispatch.

Unknown command/opcode is Unsupported. Invalid quantum is Invalid. Frontier
full and generation retirement are resource outcomes, not source invalidity.
Host/validation failures and internal invariant failures are recorded separately.

The model's reusable records are observations of ownership, not affine payload
objects. State and unique frontier membership enforce transfer in this bounded
interpreter. This does not establish general Type ownership or Data lifetime.

## Acceptance and limits

Freeze literal final observations before implementation; then require the seed
model's complete per-command/per-phase observations to match actual device
readback. Native and Bun seed execution must agree. WGSL mutants must compile
and fail a named observation on hardware; null-backend validation is not a kill.
Check every word outside the configured record/queue capacities. A fresh replay
writes only ignored output and leaves all tracked receipts unchanged.

R5 waits: this instruction subset has no owning capture environment, shared Data
lifetime, ordered n-ary join allocation, cancellation attempt ID or resumable
drop protocol. Reusing a slot generation does not solve cancelled-attempt
identity. The existing binary numeric captures remain regression controls.
R3/R7 and a mixed-field capture contract must precede a general R5 claim.
