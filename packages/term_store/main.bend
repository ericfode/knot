import Base
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V

type Id is Data:
  Id{scope: U32, slot: U32}

type Error is Data:
  WrongScope{}
  Bounds{}
  Limit{}
  ScopeExhausted{}
  InvalidTransition{}
  NotReady{}

type Scopes is Type:
  Scopes{next: U32, available: Bool}

type Store<-T: Data> is Type:
  Store{scope: U32, cells: V.Vec<T>}

type Cell<-T: Data,-E: Data> is Data:
  Pending{}
  Evaluating{}
  Ready{value: T}
  Failed{error: E}

type Action<-T: Data,-E: Data> is Data:
  Begin{}
  Succeed{value: T}
  Reject{error: E}
  Cancel{}

# Pure public transition kernel. Rejection always returns the original cell.
type Memo<-T: Data,-E: Data> is Type:
  Memo{store: Store<Cell<T,E>>}

def Scopes.from(next: U32) -> Scopes:
  Scopes{next,True{}}

def claim_fresh(+next: U32, last: Bool) -> Scopes & Result<Error,U32>:
  match last:
    case True{}:
      (Scopes{next,False{}},Done{next})
    case False{}:
      (Scopes{U32.add(next,1),True{}},Done{next})

def make_store(-T: Data, scope: Result<Error,U32>, limit: U32) -> Result<Error,Store<T>>:
  match scope:
    case Fail{e}:
      Fail{e}
    case Done{s}:
      Done{Store{s,V.Vec.bounded(T,limit)}}

def vector_error(e: V.Error) -> Error:
  match e:
    case V.Bounds{}:
      Bounds{}
    case V.Empty{}:
      Bounds{}
    case V.Limit{}:
      Limit{}
    case V.InvalidRange{}:
      Bounds{}

def Cell.step(-T: Data,-E: Data,+cell: Cell<T,E>, action: Action<T,E>) -> Cell<T,E> & Result<Error,Unit>:
  match cell:
    case Pending{}:
      match action:
        case Begin{}:
          (Evaluating{},Done{Unit{}})
        case Succeed{x}:
          (Pending{},Fail{InvalidTransition{}})
        case Reject{e}:
          (Pending{},Fail{InvalidTransition{}})
        case Cancel{}:
          (Pending{},Fail{InvalidTransition{}})
    case Evaluating{}:
      match action:
        case Begin{}:
          (Evaluating{},Fail{InvalidTransition{}})
        case Succeed{x}:
          (Ready{x},Done{Unit{}})
        case Reject{e}:
          (Failed{e},Done{Unit{}})
        case Cancel{}:
          (Pending{},Done{Unit{}})
    case Ready{+x}:
      (Ready{x},Fail{InvalidTransition{}})
    case Failed{+e}:
      (Failed{e},Fail{InvalidTransition{}})

def Cell.result(-T: Data,-E: Data,cell: Cell<T,E>) -> Result<Error,Result<E,T>>:
  match cell:
    case Pending{}:
      Fail{NotReady{}}
    case Evaluating{}:
      Fail{NotReady{}}
    case Ready{x}:
      Done{Done{x}}
    case Failed{e}:
      Done{Fail{e}}

def make_memo(-T: Data,-E: Data,r: Result<Error,Store<Cell<T,E>>>) -> Result<Error,Memo<T,E>>:
  match r:
    case Fail{e}:
      Fail{e}
    case Done{s}:
      Done{Memo{s}}

def metadata(-T: Data,k: U32,p: V.Vec<T> & U32) -> Store<T> & U32:
  (v,n) = p
  (Store{k,v},n)

def snapshot_done(-T: Data,k: U32,p: V.Vec<T> & List<T>) -> Store<T> & List<T>:
  (v,xs) = p
  (Store{k,v},xs)

def memo_wrap(-T: Data,-E: Data,-R: Type,p: Store<Cell<T,E>> & Result<Error,R>) -> Memo<T,E> & Result<Error,R>:
  (s,r) = p
  (Memo{s},r)

def Scopes.new() -> Scopes:
  Scopes.from(0)

def claim_available(+next: U32, available: Bool) -> Scopes & Result<Error,U32>:
  match available:
    case False{}:
      (Scopes{next,False{}},Fail{ScopeExhausted{}})
    case True{}:
      claim_fresh(next,U32.is_eq(next,4294967295))

def Store.length(-T: Data, s: Store<T>) -> Store<T> & U32:
  match s:
    case Store{k,v}:
      metadata(T,k,V.Vec.length(T,v))

def Store.limit(-T: Data, s: Store<T>) -> Store<T> & U32:
  match s:
    case Store{k,v}:
      metadata(T,k,V.Vec.limit(T,v))

def mapped(-T: Type, r: Result<V.Error,T>) -> Result<Error,T>:
  match r:
    case Fail{e}:
      Fail{vector_error(e)}
    case Done{x}:
      Done{x}

def allocated(scope: U32, slot: U32, r: Result<V.Error,Unit>) -> Result<Error,Id>:
  match r:
    case Fail{e}:
      Fail{vector_error(e)}
    case Done{u}:
      Done{Id{scope,slot}}

def Store.snapshot(-T: Data, s: Store<T>) -> Store<T> & List<T>:
  match s:
    case Store{k,v}:
      snapshot_done(T,k,V.Vec.to_list(T,v))

def memo_observed(-T: Data,-E: Data,r: Result<Error,Cell<T,E>>) -> Result<Error,Result<E,T>>:
  match r:
    case Fail{e}:
      Fail{e}
    case Done{c}:
      Cell.result(T,E,c)

def new_claimed(-T: Data,limit: U32,p: Scopes & Result<Error,U32>) -> Scopes & Result<Error,Store<T>>:
  (s,r) = p
  (s,make_store(T,r,limit))

def memo_new_done(-T: Data,-E: Data,p: Scopes & Result<Error,Store<Cell<T,E>>>) -> Scopes & Result<Error,Memo<T,E>>:
  (s,r) = p
  (s,make_memo(T,E,r))

def Scopes.claim(s: Scopes) -> Scopes & Result<Error,U32>:
  match s:
    case Scopes{n,a}:
      claim_available(n,a)

def alloc_pushed(-T: Data,+k: U32,n: U32,p: V.Vec<T> & Result<V.Error,Unit>) -> Store<T> & Result<Error,Id>:
  (v,r) = p
  (Store{k,v},allocated(k,n,r))

def observed(-T: Data,-R: Type,k: U32,p: V.Vec<T> & Result<V.Error,R>) -> Store<T> & Result<Error,R>:
  (v,r) = p
  (Store{k,v},mapped(R,r))

def memo_result_done(-T: Data,-E: Data,p: Memo<T,E> & Result<Error,Cell<T,E>>) -> Memo<T,E> & Result<Error,Result<E,T>>:
  (m,r) = p
  (m,memo_observed(T,E,r))
def Store.new(-T: Data, scopes: Scopes, limit: U32) -> Scopes & Result<Error,Store<T>>:
  new_claimed(T,limit,Scopes.claim(scopes))

def get_scoped(-T: Data, k: U32, v: V.Vec<T>, i: U32, valid: Bool) -> Store<T> & Result<Error,T>:
  match valid:
    case False{}:
      (Store{k,v},Fail{WrongScope{}})
    case True{}:
      observed(T,T,k,V.Vec.get(T,v,i))

def set_scoped(-T: Data, k: U32, v: V.Vec<T>, i: U32, x: T, valid: Bool) -> Store<T> & Result<Error,Unit>:
  match valid:
    case False{}:
      (Store{k,v},Fail{WrongScope{}})
    case True{}:
      observed(T,Unit,k,V.Vec.set(T,v,i,x))

def alloc_length(-T: Data,+k: U32,x: T,p: V.Vec<T> & U32) -> Store<T> & Result<Error,Id>:
  (v,n) = p
  alloc_pushed(T,k,n,V.Vec.push(T,v,x))

def Store.alloc(-T: Data, s: Store<T>, value: T) -> Store<T> & Result<Error,Id>:
  match s:
    case Store{+k,v}:
      alloc_length(T,k,value,V.Vec.length(T,v))

def Store.get(-T: Data, s: Store<T>, id: Id) -> Store<T> & Result<Error,T>:
  match s:
    case Store{+k,v}:
      match id:
        case Id{j,i}:
          get_scoped(T,k,v,i,U32.is_eq(k,j))

def Store.set(-T: Data, s: Store<T>, id: Id, value: T) -> Store<T> & Result<Error,Unit>:
  match s:
    case Store{+k,v}:
      match id:
        case Id{j,i}:
          set_scoped(T,k,v,i,value,U32.is_eq(k,j))

def Memo.new(-T: Data,-E: Data,scopes: Scopes,limit: U32) -> Scopes & Result<Error,Memo<T,E>>:
  memo_new_done(T,E,Store.new(Cell<T,E>,scopes,limit))

def Memo.alloc(-T: Data,-E: Data,m: Memo<T,E>) -> Memo<T,E> & Result<Error,Id>:
  match m:
    case Memo{s}:
      memo_wrap(T,E,Id,Store.alloc(Cell<T,E>,s,Pending{}))

def Memo.inspect(-T: Data,-E: Data,m: Memo<T,E>,id: Id) -> Memo<T,E> & Result<Error,Cell<T,E>>:
  match m:
    case Memo{s}:
      memo_wrap(T,E,Cell<T,E>,Store.get(Cell<T,E>,s,id))

def memo_commit(-T: Data,-E: Data,s: Store<Cell<T,E>>,id: Id,cell: Cell<T,E>,r: Result<Error,Unit>) -> Memo<T,E> & Result<Error,Unit>:
  match r:
    case Fail{e}:
      (Memo{s},Fail{e})
    case Done{u}:
      memo_wrap(T,E,Unit,Store.set(Cell<T,E>,s,id,cell))

def Memo.result(-T: Data,-E: Data,m: Memo<T,E>,id: Id) -> Memo<T,E> & Result<Error,Result<E,T>>:
  memo_result_done(T,E,Memo.inspect(T,E,m,id))

# First-order continuations keep computed pair elimination explicit in Bend.
def memo_stepped(-T: Data,-E: Data,s: Store<Cell<T,E>>,id: Id,p: Cell<T,E> & Result<Error,Unit>) -> Memo<T,E> & Result<Error,Unit>:
  (c,r) = p
  memo_commit(T,E,s,id,c,r)

def memo_found(-T: Data,-E: Data,s: Store<Cell<T,E>>,id: Id,action: Action<T,E>,r: Result<Error,Cell<T,E>>) -> Memo<T,E> & Result<Error,Unit>:
  match r:
    case Fail{e}:
      (Memo{s},Fail{e})
    case Done{c}:
      memo_stepped(T,E,s,id,Cell.step(T,E,c,action))

def memo_read(-T: Data,-E: Data,id: Id,action: Action<T,E>,p: Store<Cell<T,E>> & Result<Error,Cell<T,E>>) -> Memo<T,E> & Result<Error,Unit>:
  (s,r) = p
  memo_found(T,E,s,id,action,r)

def Memo.apply(-T: Data,-E: Data,m: Memo<T,E>,+id: Id,action: Action<T,E>) -> Memo<T,E> & Result<Error,Unit>:
  match m:
    case Memo{s}:
      memo_read(T,E,id,action,Store.get(Cell<T,E>,s,id))

def Memo.begin(-T: Data,-E: Data,m: Memo<T,E>,id: Id) -> Memo<T,E> & Result<Error,Unit>:
  Memo.apply(T,E,m,id,Begin{})

def Memo.succeed(-T: Data,-E: Data,m: Memo<T,E>,id: Id,value: T) -> Memo<T,E> & Result<Error,Unit>:
  Memo.apply(T,E,m,id,Succeed{value})

def Memo.fail(-T: Data,-E: Data,m: Memo<T,E>,id: Id,error: E) -> Memo<T,E> & Result<Error,Unit>:
  Memo.apply(T,E,m,id,Reject{error})

def Memo.cancel(-T: Data,-E: Data,m: Memo<T,E>,id: Id) -> Memo<T,E> & Result<Error,Unit>:
  Memo.apply(T,E,m,id,Cancel{})

