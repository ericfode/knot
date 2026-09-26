# Abstract binary join: bounded review packet

Scope: model.bend, LAWS.bend, PROOF.bend, conformance.bend. This is a sequential
Data-payload reference model, not an optimized package, affine owning store,
concurrent join, or checked GPU implementation.

## Contract, domain, and complete public surface

For arbitrary `T:Data`, Join<T> has Open, Left(value), Right(value),
Ready(left,right), and Taken states. Update is Accept(state) or Reject(state).
Taken result is Wait(state), Yield(state,left,right), or Denied(state).

`left(T,state,x)` fills Open→Left(x) or Right(y)→Ready(x,y). Other states reject
with the old state unchanged. `right` fills Open→Right(x) or
Left(y)→Ready(y,x), otherwise rejects unchanged. Duplicate payload x may be
discarded: Data payloads and this model's contract permit that. This does not
specify ownership of rejected affine handles.

`state(T,update)` projects the state of either Accept or Reject. `take(T,state)`
waits and preserves each incomplete state, yields (Taken,a,b) from Ready(a,b),
and denies Taken without changing it. `after_take(T,result)` projects its state.
These five functions are the entire exported operation family.

Input and returned states are Data. The protocol requires threading the returned
state. It does not stop a caller from keeping an old Ready snapshot and applying
take again. The one-time-take equation is about state progression, not a global
linear-ownership guarantee.

## Laws / coverage

Eighteen laws cover: left and right on all five states (10); take on all five
states (5); completion-order independence; complete payload observation; and a
second take of the returned state (3). Free payloads are arbitrary T values.
No antecedent requires an impossible state or unsafe inhabitant.

| Operation | Equations |
|---|---|
| left | Open→Accept(Left(x)); Right(b)→Accept(Ready(x,b)); Left(a)→Reject(Left(a)); Ready(a,b)→Reject(Ready(a,b)); Taken→Reject(Taken). |
| right | Open→Accept(Right(x)); Left(a)→Accept(Ready(a,x)); Right(b)→Reject(Right(b)); Ready(a,b)→Reject(Ready(a,b)); Taken→Reject(Taken). |
| take | Open/Left/Right→Wait(same); Ready(a,b)→Yield(Taken,a,b); Taken→Denied(Taken). |
| state | state(right(state(left(Open,a)),b)) = state(left(state(right(Open,b)),a)). |
| composition | take(state(right(state(left(Open,a)),b))) = Yield(Taken,a,b). |
| after_take | take(after_take(take(Ready(a,b)))) = Denied(Taken). |

These are definitional equations of an abstract transition model with generic
payloads. PROOF.bend fills all 18; the pinned upstream compiler reports
All terms check. There is no induction over arbitrary traces or concrete
runtime refinement theorem. The expected abstract constructors and ordered
payloads specify observations independently of future optimized storage.
An independent optimized implementation does not exist in this directory.

Inhabited witnesses: T=U32, payloads 7 and 9, and boundary values 0/4294967295.
All five control states are reachable. Ten JS/native observations include both
arrival orders, two duplicate rejections retaining the original value,
successful ordered take, denied second take, each incomplete state, and extrema.
The transcript is explicitly expected and compares ordered values/status;
there is no commutative-sum-only oracle. Ready/Taken delivery branches have
quantified laws but are not separately executed in the ten observations.

## Mutation and trust

Four altered models still typecheck but fail named laws and alter an executed
witness: swapping slots, overwriting a duplicate, allowing another take, and
finishing before the right result exists. evidence.json records exact source
hashes, diagnostic, and witness output. Type errors are harness failures, not
semantic kills. No new axioms or unsafe proof bodies were used. Base and the
upstream checker and native/JS code generators remain trusted.

Hostile caller: retaining an old Data state defeats a global once-only claim;
we explicitly make no such claim. A real runtime needs an affine owner or slot
invalidation plus lifetime discipline. Confluence/ownership/publication of
concurrent executions remains unverified here. Failure propagation,
cancellation, N-ary joins, allocation, and GPU performance are not exported or
promised by this model.

Live Perch review must inspect this packet as the complete declared scope;
it must not infer a concurrent or optimized implementation from the word join.
The wrapper records the packet hash and results; ../PERCH_REPORT.md records
adjudications. Evidence source hashes are in evidence.json.
