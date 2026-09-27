import Base

type Error is Data:
  Limit{}
  Full{}
  Bounds{}
  WrongArena{}
  Stale{}
  Vacant{}
  Occupied{}
  Retired{}
type Locator is Data:
  Locator{arena: U32, slot: U32, generation: U32}
type Cell<-A: Type> is Type:
  Free{generation: U32}
  Live{generation: U32, value: A}
  Dead{}
type Store<-A: Type> is Type:
  Store{arena: U32, capacity: U32, ceiling: U32, free: List<&2,U32>, cells: Array<Cell<A>>}
type Put<-A: Type> is Type:
  Placed{store: Store<A>, key: Locator}
  PutFailed{store: Store<A>, error: Error, value: A}
type Take<-A: Type> is Type:
  Taken{store: Store<A>, value: A}
  TakeFailed{store: Store<A>, error: Error}
type Placing<-A: Type> is Type:
  Installed{cell: Cell<A>, generation: U32}
  Denied{cell: Cell<A>, error: Error, value: A}
type Taking<-A: Type> is Type:
  Removed{cell: Cell<A>, reusable: Bool, value: A}
  Unchanged{cell: Cell<A>, error: Error}

def empty(fuel: Nat, -A: Type) -> Array<Cell<A>>:
  match fuel:
    case 0n: ALeaf{Free{0}}
    case 1n+ +n: ANode{empty(n,A),empty(n,A)}

def indices(fuel: Nat, +index: U32) -> List<&2,U32>:
  match fuel:
    case 0n: Nil{}
    case 1n+n: Con{index,indices(n,U32.add(index,1))}

def depth(fuel: Nat, +capacity: U32, +size: U32, +height: Nat) -> Nat:
  match fuel:
    case 0n: height
    case 1n+n:
      Bool.pick(Nat,U32.is_ge(size,capacity),height,depth(n,capacity,U32.add(size,size),1n+height))

def bounded(valid: Bool, -A: Type, arena: U32, +capacity: U32, ceiling: U32) -> Result<&2,&1,Error,Store<A>>:
  match valid:
    case False{}: Fail{Limit{}}
    case True{}:
      Done{Store{arena,capacity,ceiling,indices(U32.to_nat(capacity),0),empty(depth(12n,capacity,1,0n),A)}}

def new(-A: Type, arena: U32, +capacity: U32, ceiling: U32) -> Result<&2,&1,Error,Store<A>>:
  bounded(U32.is_le(capacity,4096),A,arena,capacity,ceiling)

def without(ids: List<&2,U32>, +index: U32) -> List<&2,U32>:
  match ids:
    case Nil{}: Nil{}
    case Con{+head,tail}:
      +rest = without(tail,index)
      Bool.pick(List<&2,U32>,U32.is_eq(head,index),rest,Con{head,rest})

def place(-A: Type, cell: Cell<A>, value: A) -> Placing<A>:
  match cell:
    case Free{+generation}: Installed{Live{generation,value},generation}
    case Live{generation,previous}: Denied{Live{generation,previous},Occupied{},value}
    case Dead{}: Denied{Dead{},Retired{},value}

def vacant(reusable: Bool, -A: Type, generation: U32, value: A) -> Taking<A>:
  match reusable:
    case True{}: Removed{Free{U32.add(generation,1)},True{},value}
    case False{}: Removed{Dead{},False{},value}

def remove_live(valid: Bool, -A: Type, +generation: U32, ceiling: U32, value: A) -> Taking<A>:
  match valid:
    case True{}: vacant(U32.is_lt(generation,ceiling),A,generation,value)
    case False{}: Unchanged{Live{generation,value},Stale{}}

def remove_free(valid: Bool, -A: Type, generation: U32) -> Taking<A>:
  match valid:
    case True{}: Unchanged{Free{generation},Vacant{}}
    case False{}: Unchanged{Free{generation},Stale{}}

def remove(-A: Type, cell: Cell<A>, +generation: U32, ceiling: U32) -> Taking<A>:
  match cell:
    case Free{+current}: remove_free(U32.is_eq(current,generation),A,current)
    case Live{+current,value}: remove_live(U32.is_eq(current,generation),A,current,ceiling,value)
    case Dead{}: Unchanged{Dead{},Retired{}}

def placed(-A: Type, +arena: U32, capacity: U32, ceiling: U32,
  free: List<&2,U32>, next: List<&2,U32>, cells: Array<Cell<A>>, +index: U32, result: Placing<A>) -> Put<A>:
  match result:
    case Installed{cell,generation}:
      Placed{Store{arena,capacity,ceiling,next,Array.set(Cell<A>,cells,index,cell)},Locator{arena,index,generation}}
    case Denied{cell,error,value}:
      PutFailed{Store{arena,capacity,ceiling,free,Array.set(Cell<A>,cells,index,cell)},error,value}

def insertion(-A: Type, arena: U32, capacity: U32, ceiling: U32,
  free: List<&2,U32>, next: List<&2,U32>, index: U32, value: A, pair: Array<Cell<A>> & Cell<A>) -> Put<A>:
  (cells,previous) = pair
  placed(A,arena,capacity,ceiling,free,next,cells,index,place(A,previous,value))

def put_bound(valid: Bool, -A: Type, store: Store<A>, +index: U32, value: A) -> Put<A>:
  match valid store:
    case False{} _: PutFailed{store,Bounds{},value}
    case True{} Store{arena,capacity,ceiling,+free,cells}:
      insertion(A,arena,capacity,ceiling,free,without(free,index),index,value,Array.swap(Cell<A>,cells,index,Dead{}))

def put(-A: Type, store: Store<A>, +index: U32, value: A) -> Put<A>:
  match store:
    case Store{arena,+capacity,ceiling,free,cells}:
      put_bound(U32.is_lt(index,capacity),A,Store{arena,capacity,ceiling,free,cells},index,value)

def alloc(-A: Type, store: Store<A>, value: A) -> Put<A>:
  match store:
    case Store{arena,capacity,ceiling,Nil{},cells}: PutFailed{Store{arena,capacity,ceiling,Nil{},cells},Full{},value}
    case Store{arena,capacity,ceiling,Con{+index,+tail},cells}:
      insertion(A,arena,capacity,ceiling,Con{index,tail},tail,index,value,Array.swap(Cell<A>,cells,index,Dead{}))

def returned(-A: Type, arena: U32, capacity: U32, ceiling: U32,
  +free: List<&2,U32>, cells: Array<Cell<A>>, +index: U32, result: Taking<A>) -> Take<A>:
  match result:
    case Removed{cell,reusable,value}:
      Taken{Store{arena,capacity,ceiling,Bool.pick(List<&2,U32>,reusable,Con{index,free},free),Array.set(Cell<A>,cells,index,cell)},value}
    case Unchanged{cell,error}:
      TakeFailed{Store{arena,capacity,ceiling,free,Array.set(Cell<A>,cells,index,cell)},error}

def extraction(-A: Type, arena: U32, capacity: U32, +ceiling: U32,
  free: List<&2,U32>, index: U32, generation: U32, pair: Array<Cell<A>> & Cell<A>) -> Take<A>:
  (cells,previous) = pair
  returned(A,arena,capacity,ceiling,free,cells,index,remove(A,previous,generation,ceiling))

def take_bound(valid: Bool, -A: Type, store: Store<A>, +index: U32, generation: U32) -> Take<A>:
  match valid store:
    case False{} _: TakeFailed{store,Bounds{}}
    case True{} Store{arena,capacity,ceiling,free,cells}:
      extraction(A,arena,capacity,ceiling,free,index,generation,Array.swap(Cell<A>,cells,index,Dead{}))

def take_arena(valid: Bool, -A: Type, store: Store<A>, +index: U32, generation: U32) -> Take<A>:
  match valid store:
    case False{} _: TakeFailed{store,WrongArena{}}
    case True{} Store{arena,+capacity,ceiling,free,cells}:
      take_bound(U32.is_lt(index,capacity),A,Store{arena,capacity,ceiling,free,cells},index,generation)

def take(-A: Type, store: Store<A>, key: Locator) -> Take<A>:
  match store key:
    case Store{+arena,capacity,ceiling,free,cells} Locator{realm,index,generation}:
      take_arena(U32.is_eq(arena,realm),A,Store{arena,capacity,ceiling,free,cells},index,generation)

def disposed(-A: Type, -B: Data, result: Take<A>, dispose: A -> B) -> Store<A> & Result<Error,B>:
  match result:
    case Taken{store,value}: (store,Done{dispose(value)})
    case TakeFailed{store,error}: (store,Fail{error})

def release(-A: Type, -B: Data, store: Store<A>, key: Locator, dispose: A -> B) -> Store<A> & Result<Error,B>:
  disposed(A,B,take(A,store,key),dispose)
