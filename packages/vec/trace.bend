import Base
import ./main.bend as V
import ./model.bend as M

def err(e: V.Error) -> M.Observation:
  match e:
    case V.Bounds{}: M.BadIndex{}
    case V.Empty{}: M.IsEmpty{}
    case V.Limit{}: M.AtLimit{}
    case V.InvalidRange{}: M.BadRange{}

def unit_result(r: Result<V.Error,Unit>) -> M.Observation:
  match r:
    case Fail{e}: err(e)
    case Done{u}: M.Ok{}

def value_result(r: Result<V.Error,U32>) -> M.Observation:
  match r:
    case Fail{e}: err(e)
    case Done{x}: M.Value{x}

def data_list(xs: List<U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{x,t}: Con{x,data_list(t)}

def list_result(r: Result<V.Error,List<U32>>) -> M.Observation:
  match r:
    case Fail{e}: err(e)
    case Done{xs}: M.Values{data_list(xs)}

def unit_pair(pair: V.Vec<U32> & Result<V.Error,Unit>) -> V.Vec<U32> & M.Observation:
  (v,r) = pair
  (v,unit_result(r))

def value_pair(pair: V.Vec<U32> & Result<V.Error,U32>) -> V.Vec<U32> & M.Observation:
  (v,r) = pair
  (v,value_result(r))

def list_pair(pair: V.Vec<U32> & Result<V.Error,List<U32>>) -> V.Vec<U32> & M.Observation:
  (v,r) = pair
  (v,list_result(r))

def step(v: V.Vec<U32>, op: M.Op) -> V.Vec<U32> & M.Observation:
  match op:
    case M.Push{x}: unit_pair(V.Vec.push(U32,v,x))
    case M.Pop{}: value_pair(V.Vec.pop(U32,v))
    case M.Get{i}: value_pair(V.Vec.get(U32,v,i))
    case M.Set{i,x}: unit_pair(V.Vec.set(U32,v,i,x))
    case M.Swap{i,x}: value_pair(V.Vec.swap(U32,v,i,x))
    case M.Reserve{n}: unit_pair(V.Vec.reserve(U32,v,n))
    case M.Slice{s,e}: list_pair(V.Vec.slice(U32,v,s,e))

type Snapshot is Data:
  Snapshot{xs: List<&2,U32>, len: U32, cap: U32, max: U32}

def snapshot_limit(xs: List<&2,U32>, n: U32, c: U32, pair: V.Vec<U32> & U32) -> V.Vec<U32> & Snapshot:
  (v,m) = pair
  (v,Snapshot{xs,n,c,m})

def snapshot_cap(xs: List<&2,U32>, n: U32, pair: V.Vec<U32> & U32) -> V.Vec<U32> & Snapshot:
  (v,c) = pair
  snapshot_limit(xs,n,c,V.Vec.limit(U32,v))

def snapshot_len(xs: List<&2,U32>, pair: V.Vec<U32> & U32) -> V.Vec<U32> & Snapshot:
  (v,n) = pair
  snapshot_cap(xs,n,V.Vec.capacity(U32,v))

def snapshot_list(pair: V.Vec<U32> & List<U32>) -> V.Vec<U32> & Snapshot:
  (v,xs) = pair
  snapshot_len(data_list(xs),V.Vec.length(U32,v))

def snapshot(v: V.Vec<U32>) -> V.Vec<U32> & Snapshot:
  snapshot_list(V.Vec.to_list(U32,v))

def state_eq(state: M.State, snap: Snapshot) -> Bool:
  match state:
    case M.Sequence{+xs,+m}:
      match snap:
        case Snapshot{ys,+n,+c,q}:
          Bool.and(M.list_eq(xs,ys),Bool.and(U32.is_eq(M.length(xs),n),
            Bool.and(U32.is_eq(m,q),Bool.and(U32.is_le(n,m),Bool.and(U32.is_le(n,c),
              Bool.and(U32.is_le(c,V.Vec.maximum()),Bool.and(U32.is_ne(c,0),U32.is_eq(U32.and(c,U32.sub(c,1)),0))))))))

# Capacity is tested independently from the list oracle. Exact minimum power
# is characterized by need <= cap and, when cap grows, cap/2 < need.
def capacity_ok(old: U32, +now: U32, +need: U32, grew: Bool) -> Bool:
  match grew:
    case False{}:
      U32.is_eq(old,now)
    case True{}:
      Bool.and(U32.is_le(need,now),U32.is_lt(U32.shr(now),need))

def capacity_need(+old: U32, +now: U32, +need: U32) -> Bool:
  capacity_ok(old,now,need,U32.is_lt(old,need))

def capacity_op(+old: U32, +now: U32, n: U32, op: M.Op, observation: M.Observation) -> Bool:
  match op:
    case M.Push{x}:
      match observation:
        case M.Ok{}: capacity_need(old,now,n)
        case _: U32.is_eq(old,now)
    case M.Reserve{need}:
      match observation:
        case M.Ok{}: capacity_need(old,now,need)
        case _: U32.is_eq(old,now)
    case _: U32.is_eq(old,now)

def compare_step(old: U32, op: M.Op, +actual: M.Observation, expected: M.Observation,
  +state: M.State, pair: V.Vec<U32> & Snapshot) -> (V.Vec<U32> & M.State) & Bool:
  (v,+snap) = pair
  match snap:
    case Snapshot{xs,n,c,m}:
      ((v,state),Bool.and(M.obs_eq(actual,expected),Bool.and(state_eq(state,snap),capacity_op(old,c,n,op,actual))))

def run_step(old: U32, op: M.Op, impl: V.Vec<U32> & M.Observation,
  model: M.State & M.Observation) -> (V.Vec<U32> & M.State) & Bool:
  (v,a) = impl
  (s,b) = model
  compare_step(old,op,a,b,s,snapshot(v))

def from_snapshot(+op: M.Op, state: M.State, pair: V.Vec<U32> & Snapshot) -> (V.Vec<U32> & M.State) & Bool:
  (v,snap) = pair
  match snap:
    case Snapshot{xs,n,c,m}:
      run_step(c,op,step(v,op),M.step(state,op))

def run(ops: List<&2,M.Op>, state: (V.Vec<U32> & M.State) & Bool) -> Bool:
  match ops:
    case Nil{}:
      (s,ok) = state
      ok
    case Con{op,tail}:
      ((v,m),ok) = state
      Bool.and(ok,run(tail,from_snapshot(op,m,snapshot(v))))

def trace(+limit: U32, ops: List<&2,M.Op>) -> Bool:
  run(ops,((V.Vec.bounded(U32,limit),M.Sequence{Nil{},U32.min(limit,V.Vec.maximum())}),True{}))
