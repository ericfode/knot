# TermStore interface — 2026-09-26

Status: published and verified from a fresh remote cache on CPU and JavaScript. Depends on
verified Vec `0xd684886d10b431b9dce6c3b2d1ef1980/main.bend`. No IntMap dependency. All payloads are first-order `Data`.

Published API: `import 0xce7bfa94c40ded8493cdb39d330add0c/main.bend as S`.
Published proof/release entry: `import 0xce7bfa94c40ded8493cdb39d330add0c/release.bend as TermStoreRelease`.

```
Id : Data = Id{scope: U32, slot: U32}
Error : Data = WrongScope | Bounds | Limit | ScopeExhausted | InvalidTransition | NotReady
Scopes : Type                         # affine lifetime allocator
Scopes.new() -> Scopes                # one root per identity-comparison realm
Scopes.from(next: U32) -> Scopes       # explicit restored/test root; same uniqueness obligation
Store<T: Data> : Type
Store.new(-T, scopes: Scopes, limit: U32) -> Scopes & Result<Error, Store<T>>
Store.length(-T, store) -> Store<T> & U32
Store.limit(-T, store) -> Store<T> & U32
Store.alloc(-T, store, value: T) -> Store<T> & Result<Error, Id>
Store.get(-T, store, id: Id) -> Store<T> & Result<Error, T>
Store.set(-T, store, id: Id, value: T) -> Store<T> & Result<Error, Unit>
Store.snapshot(-T, store) -> Store<T> & List<T>
Cell<T: Data,E: Data> : Data = Pending | Evaluating | Ready{value:T} | Failed{error:E}
Memo<T: Data,E: Data> : Type
Memo.new(-T,-E,scopes,limit) -> Scopes & Result<Error,Memo<T,E>>
Memo.alloc(-T,-E,memo) -> Memo<T,E> & Result<Error,Id>
Memo.inspect(-T,-E,memo,id) -> Memo<T,E> & Result<Error,Cell<T,E>>
Memo.begin(-T,-E,memo,id) -> Memo<T,E> & Result<Error,Unit>
Memo.succeed(-T,-E,memo,id,value:T) -> Memo<T,E> & Result<Error,Unit>
Memo.fail(-T,-E,memo,id,error:E) -> Memo<T,E> & Result<Error,Unit>
Memo.cancel(-T,-E,memo,id) -> Memo<T,E> & Result<Error,Unit>
Memo.result(-T,-E,memo,id) -> Memo<T,E> & Result<Error,Result<E,T>>
```

`new` consumes one scope even for a zero-limit store. Scope 0xffffffff is usable;
the following `new` returns ScopeExhausted without wrapping. Stores never recycle
slots. IDs are stable through growth and writes. Their scope must match before slot
bounds are considered. Limit is clamped to Vec's 16,777,216 maximum. Allocation at
limit fails without modifying existing cells. Every operation threads its owner.

Scopes are explicit namespace tags, not globally unique pointers or security
capabilities. Use ONE Scopes chain for all stores whose IDs may meet. Reinitializing
or restoring a conflicting chain can alias IDs and is outside the uniqueness
contract. Raw numeric IDs can be fabricated, and valid numbers address that slot.
Dropping a store ends its lifetime; a later store from the SAME chain has a different
scope. Do not construct implementation containers or unwrap Memo's internal Store.

Memo transitions: Pending→Evaluating (`begin`); Evaluating→Ready (`succeed`),
Evaluating→Failed (`fail`), Evaluating→Pending (`cancel`, for interrupted work).
All other transitions return InvalidTransition and preserve every cell. Ready and
Failed are terminal. `result` returns Done(Done(value)) only for Ready;
Done(Fail(error)) only for Failed; Pending/Evaluating return Fail(NotReady).
Missing IDs are Bounds/WrongScope, never Pending or a completed value.

Expected compiled-native costs: constant metadata/get/set/memo transitions,
amortized constant allocation, linear snapshots/growth. Costs exclude copying or
dropping payload graphs. CPU and JavaScript conformance/scaling have passed locally. GPU execution has not been tested.

Supported pure kernel API:
`Action<T,E> = Begin | Succeed(T) | Reject(E) | Cancel`;
`Cell.step(-T,-E,cell,action) -> Cell<T,E> & Result<Error,Unit>`;
`Cell.result(-T,-E,cell) -> Result<Error,Result<E,T>>`;
`Memo.apply(-T,-E,memo,id,action)` is the general transition operation underlying
begin/succeed/fail/cancel. All other module helpers and container constructors are
implementation details, even though Bend has no module-level access control.

Cancel means interrupted/exhausted work, not semantic failure. The caller supplies
only complete results to succeed and only definitive errors to fail. This is a
serial ownership protocol; it provides no concurrent attempt tokens. After cancel,
the owner must discard stale work before beginning another attempt. It does not
store affine task handles, continuation queues, join handles, or GPU pointers.
Append-only slots are never reused, including while external Data IDs remain live.
Device quiescence and disposal of references before destroying the whole store
remain the owning runtime's responsibility. No GPU-safety validation is claimed.
