import Base
import ./store.bend as S

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
