import Base
import ./main.bend as S
import ./model.bend as M

def error_code(e: S.Error) -> U32:
  match e:
    case S.WrongScope{}: 1
    case S.Bounds{}: 2
    case S.Limit{}: 3
    case S.ScopeExhausted{}: 4
    case S.InvalidTransition{}: 5
    case S.NotReady{}: 6

def error_eq(a: S.Error,b: S.Error) -> Bool:
  U32.is_eq(error_code(a),error_code(b))

def id_eq(a: S.Id,b: S.Id) -> Bool:
  match a:
    case S.Id{s,i}:
      match b:
        case S.Id{t,j}:
          Bool.and(U32.is_eq(s,t),U32.is_eq(i,j))

def unit_eq(a: Result<S.Error,Unit>,b: Result<S.Error,Unit>) -> Bool:
  match a:
    case Fail{e}:
      match b:
        case Fail{f}: error_eq(e,f)
        case Done{u}: False{}
    case Done{u}:
      match b:
        case Fail{e}: False{}
        case Done{v}: True{}

def value_eq(a: Result<S.Error,U32>,b: Result<S.Error,U32>) -> Bool:
  match a:
    case Fail{e}:
      match b:
        case Fail{f}: error_eq(e,f)
        case Done{v}: False{}
    case Done{x}:
      match b:
        case Fail{e}: False{}
        case Done{y}: U32.is_eq(x,y)

def alloc_eq(a: Result<S.Error,S.Id>,b: Result<S.Error,S.Id>) -> Bool:
  match a:
    case Fail{e}:
      match b:
        case Fail{f}: error_eq(e,f)
        case Done{v}: False{}
    case Done{x}:
      match b:
        case Fail{e}: False{}
        case Done{y}: id_eq(x,y)

def values_eq(xs: List<U32>,ys: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}:
      match ys:
        case Nil{}: True{}
        case Con{y,rest}: False{}
    case Con{x,rest}:
      match ys:
        case Nil{}: False{}
        case Con{y,tail}:
          Bool.and(U32.is_eq(x,y),values_eq(rest,tail))

def snapshot_check(a: M.Arena<U32>,p: S.Store<U32> & List<U32>) -> S.Store<U32> & Bool:
  match a:
    case M.Arena{s,b,xs}:
      (store,ys) = p
      (store,values_eq(ys,xs))

def same_state(store: S.Store<U32>,a: M.Arena<U32>) -> S.Store<U32> & Bool:
  snapshot_check(a,S.Store.snapshot(U32,store))

type Op is Data:
  Alloc{x: U32}
  Read{id: S.Id}
  Write{id: S.Id,x: U32}
  Length{}
  Limit{}

def after_alloc(q: M.Arena<U32> & Result<S.Error,S.Id>,p: S.Store<U32> & Result<S.Error,S.Id>) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (a,expected) = q
  (s,actual) = p
  (s,(a,alloc_eq(actual,expected)))

def after_read(a: M.Arena<U32>,expected: Result<S.Error,U32>,p: S.Store<U32> & Result<S.Error,U32>) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (s,actual) = p
  (s,(a,value_eq(actual,expected)))

def after_write(q: M.Arena<U32> & Result<S.Error,Unit>,p: S.Store<U32> & Result<S.Error,Unit>) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (a,expected) = q
  (s,actual) = p
  (s,(a,unit_eq(actual,expected)))

def after_meta(a: M.Arena<U32>,expected: U32,p: S.Store<U32> & U32) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (s,actual) = p
  (s,(a,U32.is_eq(actual,expected)))

def model_length(a: M.Arena<U32>) -> U32:
  match a:
    case M.Arena{s,b,xs}: U32.from_nat(M.count(U32,xs))

def model_limit(a: M.Arena<U32>) -> U32:
  match a:
    case M.Arena{s,b,xs}: U32.from_nat(b)

def one(s: S.Store<U32>,+a: M.Arena<U32>,op: Op) -> S.Store<U32> & (M.Arena<U32> & Bool):
  match op:
    case Alloc{+x}: after_alloc(M.allocate(U32,a,x),S.Store.alloc(U32,s,x))
    case Read{+id}: after_read(a,M.read(U32,a,id),S.Store.get(U32,s,id))
    case Write{+id,+x}: after_write(M.write(U32,a,id,x),S.Store.set(U32,s,id,x))
    case Length{}: after_meta(a,model_length(a),S.Store.length(U32,s))
    case Limit{}: after_meta(a,model_limit(a),S.Store.limit(U32,s))

def checked_snapshot(a: M.Arena<U32>,ok: Bool,p: S.Store<U32> & Bool) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (s,good) = p
  (s,(a,Bool.and(ok,good)))

def checked_one(ok: Bool,p: S.Store<U32> & (M.Arena<U32> & Bool)) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (s,q) = p
  (+a,good) = q
  checked_snapshot(a,Bool.and(ok,good),same_state(s,a))

def advance(p: S.Store<U32> & (M.Arena<U32> & Bool),op: Op) -> S.Store<U32> & (M.Arena<U32> & Bool):
  (s,q) = p
  (a,ok) = q
  checked_one(ok,one(s,a,op))

def run(ops: List<&2,Op>,p: S.Store<U32> & (M.Arena<U32> & Bool)) -> Bool:
  match ops:
    case Nil{}:
      (s,q) = p
      (a,ok) = q
      Bool.and(ok,Pair.snd(S.Store<U32>,Bool,same_state(s,a)))
    case Con{op,rest}:
      run(rest,advance(p,op))

def started(ops: List<&2,Op>,scope: U32,bound: Nat,r: Result<S.Error,S.Store<U32>>) -> Bool:
  match r:
    case Fail{e}: False{}
    case Done{s}: run(ops,(s,(M.Arena{scope,bound,Nil{}},True{})))

def created(ops: List<&2,Op>,scope: U32,bound: Nat,p: S.Scopes & Result<S.Error,S.Store<U32>>) -> Bool:
  (scopes,r) = p
  started(ops,scope,bound,r)

def trace(ops: List<&2,Op>,+scope: U32,+bound: U32) -> Bool:
  created(ops,scope,U32.to_nat(U32.min(bound,16777216)),S.Store.new(U32,S.Scopes.from(scope),bound))

def store_witness() -> Bool:
  trace([Length{},Limit{},Read{S.Id{7,0}},Alloc{17},Alloc{29},Alloc{43},
    Read{S.Id{7,0}},Read{S.Id{7,1}},Read{S.Id{7,2}},Write{S.Id{7,1},97},
    Read{S.Id{7,0}},Read{S.Id{7,1}},Read{S.Id{7,2}},Length{},
    Write{S.Id{8,0},99},Write{S.Id{7,3},88},Write{S.Id{7,4294967295},66},
    Read{S.Id{8,4294967295}},Alloc{61},Alloc{79},Alloc{83},Length{}],7,5)

def zero_witness() -> Bool:
  trace([Alloc{11},Read{S.Id{0,0}},Write{S.Id{0,0},23},Length{},Limit{}],0,0)
