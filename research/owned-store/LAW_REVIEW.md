# Owning store: bounded review packet

This seed CPU component qualifies the R2 ownership transitions and part of R4
freshness. It is not a published runtime package or a Wasm/GPU implementation.
The accepted language of Knot remains unchanged.

## Contract and abstraction

`Store<A:Type>` holds affine payloads in a balanced `Array<Cell<A>>`, plus an
ordered free-slot list. `Locator` is reusable Data: three U32 words identifying
arena, slot and generation. A locator is not extraction authority. Operations
consume the store and return its successor; input payloads rejected by put/alloc
are returned separately. Supplied arena IDs must be unique across all lifetimes
whose locators can meet. Internal constructors are trusted construction only.

Capacity is 0..4096, checked before allocation. Array padding is inaccessible.
An empty slot starts at generation zero. Successful take increments generations
below the supplied ceiling; at the ceiling it retires the slot permanently.
The free list starts in increasing order. Put removes its index without changing
others; take prepends only a reusable index. No generation wrap is permitted.
Take validates arena, then logical bounds, then the cell state/generation.
Retired cells return Retired for every generation; vacant cells distinguish
matching Vacant from mismatching Stale. Release invokes its affine disposer on
success; failures preserve the store and never invoke it. This does not prove
physical payload reclamation or preservation of a discarded disposer closure.

The model uses only persistent Data lists, positional lookup and replacement.
It imports the Error/Locator constructors and the observation vocabulary, but
calls no store operation or optimized array helper. Its Snapshot includes arena,
logical capacity, ceiling, ordered free IDs, and every logical cell's tag,
generation and payload serial. Events include returned inputs and taken/disposed
serials. Comparing only the occupied contents would miss stale generation and
free-order defects. The implementation observer consumes Type payloads and the
store. Every trace starts fresh; snapshots never duplicate an owned store.

The protocol's serializers are shared by both lanes. Fifteen hand-written literal
observations independently constrain that shared projection. Serials distinguish
7, 9 and 11; their projection is not a model of arbitrary payload destructors.

## Coverage and domains

| API | Law evidence | Independent runtime evidence |
| --- | --- | --- |
| new | capacity 4097 rejects | 0,1,2,3,4,16,64,256,1024,4096; 4097/U32.max reject |
| put | free/occupied/retired kernels, zero-capacity rejection | old and incoming owners, padding/bounds, free-order preservation, unrelated slots |
| alloc | uses the same checked cell transition | zero/full, increasing initial IDs, reuse and permanent retirement |
| take | arbitrary-payload singleton transfer/retirement, wrong arena, stale singleton | repeated take, stale after reuse, unrelated payload preservation, arena-before-bounds, generation negatives |
| release | success applies disposer; failure preserves store | disposal serials, failed disposal, mixed take/drop traces, unrelated owners |
| generation boundary | max-1 advances to max; max retires | both public take transitions run natively and in Bun on explicitly constructed reachable near-ceiling states |
| locator versus authority | seed quantity acceptance/rejection | copied Locator passes; Store/Payload transfer passes; duplicate Store/Payload fail with `consumed more than once` |

All domains have safe witnesses: Owned{7}/Owned{9}; new stores of capacity 0/1/2;
occupied, reused and retired states constructed by public traces. Near-U32.max
states use direct internal construction to avoid billions of setup cycles; their
reachability follows the specified increment rule, not a measured long run.
No Empty premise, new axiom, unsafe cast or proof hole is introduced.

`LAWS.bend` has 14 filled equations. Generic payload/cell/disposer equations are
universal in their displayed arguments. Singleton laws normalize capacity-one
states with arbitrary erased Type payloads; capacity and word-boundary equations
use concrete numeric witnesses. They do not prove general Array refinement,
free-list invariants by induction, general state composition or allocator safety.
The complete `PROOF.bend` passes; the seed inventory reports zero holes.

`python3 research/owned-store/check.py` compares 3,532 traces on native and Bun:
all 3,510 sequences of length 0..3 from a fixed eight-command alphabet at
capacities 0..2 and ceilings 0..1; fifteen named literal witnesses; seven larger
capacity workloads. Each trace records every result and its complete final
logical state. All prefixes in the bounded exhaustive domain are independently
run. Named longer traces cover retirement and stale access after reuse. There
are also four actual backend observations at max-1/max generation and five
positive/negative quantity fixtures. These are finite results, not universal
equivalence or constant-time evidence. Width scaling completes through 4096;
the timings include construction, model work, formatting and process startup.

## Mutation and adversarial review

Six mutants remain parseable/type-correct and execute in Bun. The original
model and literal assertions reject each for the stated public observation:

| Mutation | Witness |
| --- | --- |
| reuse old generation | take-twice and stale-after-reuse |
| permit physical padding | capacity-three put at index three |
| replace occupied owner with rejected input | occupied retains 7 and returns 9 |
| ignore arena | wrong arena is rejected before oversized index |
| reuse the ceiling generation | retirement-cycle / retired-full |
| append released ID instead of prepending | free-order with another free slot |

No parser/type error, timeout or harness failure is counted as a semantic kill.
The failed first harness attempt is retained: a single 3,531-case literal exceeded
Bun's construction stack. Batching the same inputs into 32-case declarations
passed both lanes. A later added stale-after-reuse witness brought the corpus to
3,532. Assertions and runtime code were not changed to hide that failure.

A hostile caller can forge a Store constructor or reuse a caller-supplied arena
ID. These are outside the valid construction contract and are unresolved runtime
integration boundaries, not type-enforced module privacy. Same-store generation
retirement is established; global arena allocation and snapshot restore are not.
The current observer also cannot establish physical reclamation, asynchronous
reader safety, suspended-root reachability, Data sharing, or device memory order.
Those remain R3/R4/R5/R6/R7 work. No speedup, self-hosting, or GPU execution is
claimed here.

The checked seed loads 42 Base foreign declarations and unsafe Array.fork/join;
this component introduces/calls neither unsafe helper. Generated conformance
foreign calls contain only IO.print. Primitive arithmetic/array lowering, the
seed checker/normalizer and native/Bun runtimes remain trusted. Full inventories,
commands, source hashes, raw outputs and mutant failures are in receipts.

## Exact law statements supplied to review

These are the complete statements filled by PROOF.bend. `-` binds erased
Type witnesses; it grants no reusable runtime owner.

```bend
law free_accepts_owner:
  for -A: Type
  for -value: A
  for +generation: U32
  {S.place(A,S.Free{generation},value) == S.Installed{S.Live{generation,value},generation} : S.Placing<A>}

law occupied_preserves_both_owners:
  for -A: Type
  for -old: A
  for -incoming: A
  for +generation: U32
  {S.place(A,S.Live{generation,old},incoming) == S.Denied{S.Live{generation,old},S.Occupied{},incoming} : S.Placing<A>}

law retired_preserves_incoming:
  for -A: Type
  for -value: A
  {S.place(A,S.Dead{},value) == S.Denied{S.Dead{},S.Retired{},value} : S.Placing<A>}

law stale_preserves_live_owner:
  for -A: Type
  for -value: A
  for +generation: U32
  for ceiling: U32
  {S.remove_live(False{},A,generation,ceiling,value) == S.Unchanged{S.Live{generation,value},S.Stale{}} : S.Taking<A>}

law ceiling_retires_without_wrap:
  for -A: Type
  for -value: A
  {S.remove(A,S.Live{4294967295,value},4294967295,4294967295) == S.Removed{S.Dead{},False{},value} : S.Taking<A>}

law last_generation_remains_usable:
  for -A: Type
  for -value: A
  {S.remove(A,S.Live{4294967294,value},4294967294,4294967295) == S.Removed{S.Free{4294967295},True{},value} : S.Taking<A>}

law capacity_limit_is_explicit:
  for -A: Type
  {S.new(A,41,4097,1) == Fail{S.Limit{}} : Result<&2,&1,S.Error,S.Store<A>>}

law zero_capacity_preserves_incoming:
  for -A: Type
  for -value: A
  {S.put(A,S.Store{41,0,1,Nil{},ALeaf{S.Free{0}}},0,value) == S.PutFailed{S.Store{41,0,1,Nil{},ALeaf{S.Free{0}}},S.Bounds{},value} : S.Put<A>}

law singleton_take_transfers_and_advances:
  for -A: Type
  for -value: A
  {S.take(A,S.Store{41,1,1,Nil{},ALeaf{S.Live{0,value}}},S.Locator{41,0,0}) == S.Taken{S.Store{41,1,1,[0],ALeaf{S.Free{1}}},value} : S.Take<A>}

law singleton_take_retires:
  for -A: Type
  for -value: A
  {S.take(A,S.Store{41,1,0,Nil{},ALeaf{S.Live{0,value}}},S.Locator{41,0,0}) == S.Taken{S.Store{41,1,0,Nil{},ALeaf{S.Dead{}}},value} : S.Take<A>}

law wrong_arena_preserves_owner:
  for -A: Type
  for -value: A
  {S.take(A,S.Store{41,1,1,Nil{},ALeaf{S.Live{0,value}}},S.Locator{42,0,0}) == S.TakeFailed{S.Store{41,1,1,Nil{},ALeaf{S.Live{0,value}}},S.WrongArena{}} : S.Take<A>}

law stale_locator_cannot_take_twice:
  for -A: Type
  {S.take(A,S.Store{41,1,1,[0],ALeaf{S.Free{1}}},S.Locator{41,0,0}) == S.TakeFailed{S.Store{41,1,1,[0],ALeaf{S.Free{1}}},S.Stale{}} : S.Take<A>}

law failed_release_preserves_store:
  for -A: Type
  for -B: Data
  for -store: S.Store<A>
  for +error: S.Error
  for -dispose: A -> B
  {S.disposed(A,B,S.TakeFailed{store,error},dispose) == (store,Fail{error}) : S.Store<A> & Result<S.Error,B>}

law successful_release_applies_disposer:
  for -A: Type
  for -B: Data
  for -store: S.Store<A>
  for -value: A
  for -dispose: A -> B
  {S.disposed(A,B,S.Taken{store,value},dispose) == (store,Done{dispose(value)}) : S.Store<A> & Result<S.Error,B>}
```

Two literal observations illustrate the independently fixed projection:

- Capacity zero, alloc(Owned{7}): `[fail:full:7]/41;0;1;[];[]`.
- Capacity one, put(0,Owned{7}), put(0,Owned{9}):
  `[alloc:41,0,0, fail:occupied:9]/41;1;1;[];[live:0:7]`.

## Reviewed source identity

| File | SHA-256 |
| --- | --- |
| store.bend | 80f6addb26deb38d46a4abacc91e9df59f734437e4c34598919b0c4f4ca15af5 |
| model.bend | 84714c47995b76d9902e09e600b77ebb66d157bfcb864dee813b546fe8a980f1 |
| observe.bend | d3fc11af358d653d281d34388fe625bb3a6af0362fc6950dc6625d1251aa4910 |
| protocol.bend | fac9b00af588e61dd34ca257a860b41ae51b7d8e904c669de40a43127dc4d989 |
| LAWS.bend | 9859e42fce02b73eba69e035ecc957bf69f31167b846f891d7a60c7ffb4496f8 |
| PROOF.bend | ac0effe0eef99f90316b737b74c9884b003d2b46d810e8fc68a7ecb33bad2b2a |
