import Base

type Error is Data:
  Bounds{}
  Empty{}
  Limit{}
  InvalidRange{}

type Vec<-T: Data> is Type:
  Buffer{len: U32, cap: U32, depth: Nat, max: U32, slots: Array<Maybe<&2, T>>}

def Vec.maximum() -> U32:
  16777216

def Vec.bounded(-T: Data, limit: U32) -> Vec<T>:
  Buffer{0, 1, 0n, U32.min(limit, Vec.maximum()), Array.new(Maybe<&2,T>, 0n, None{})}

def Vec.new(-T: Data) -> Vec<T>:
  Vec.bounded(T, Vec.maximum())

def Vec.length(-T: Data, v: Vec<T>) -> Vec<T> & U32:
  match v:
    case Buffer{+n,c,d,m,a}:
      (Buffer{n,c,d,m,a}, n)

def Vec.capacity(-T: Data, v: Vec<T>) -> Vec<T> & U32:
  match v:
    case Buffer{n,+c,d,m,a}:
      (Buffer{n,c,d,m,a}, c)

def Vec.limit(-T: Data, v: Vec<T>) -> Vec<T> & U32:
  match v:
    case Buffer{n,c,d,+m,a}:
      (Buffer{n,c,d,m,a}, m)

def slot_result(-T: Data, x: Maybe<&2,T>) -> Result<Error,T>:
  match x:
    case None{}:
      Fail{Bounds{}}
    case Some{v}:
      Done{v}

def observed(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  r: Array<Maybe<&2,T>> & Maybe<&2,T>) -> Vec<T> & Result<Error,T>:
  (a,x) = r
  (Buffer{n,c,d,m,a},slot_result(T,x))

def get_if(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, i: U32, valid: Bool) -> Vec<T> & Result<Error,T>:
  match valid:
    case False{}:
      (Buffer{n,c,d,m,a}, Fail{Bounds{}})
    case True{}:
      observed(T,n,c,d,m,Array.get(Maybe<&2,T>,a,i))

def Vec.get(-T: Data, v: Vec<T>, +index: U32) -> Vec<T> & Result<Error,T>:
  match v:
    case Buffer{+n,c,d,m,a}:
      get_if(T,n,c,d,m,a,index,U32.is_lt(index,n))

def swap_if(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, i: U32, value: T, valid: Bool) -> Vec<T> & Result<Error,T>:
  match valid:
    case False{}:
      (Buffer{n,c,d,m,a}, Fail{Bounds{}})
    case True{}:
      observed(T,n,c,d,m,Array.swap(Maybe<&2,T>,a,i,Some{value}))

def Vec.swap(-T: Data, v: Vec<T>, +index: U32, value: T) -> Vec<T> & Result<Error,T>:
  match v:
    case Buffer{+n,c,d,m,a}:
      swap_if(T,n,c,d,m,a,index,value,U32.is_lt(index,n))

def discard_value(-T: Data, r: Result<Error,T>) -> Result<Error,Unit>:
  match r:
    case Fail{e}:
      Fail{e}
    case Done{x}:
      Done{Unit{}}

def set_result(-T: Data, pair: Vec<T> & Result<Error,T>) -> Vec<T> & Result<Error,Unit>:
  (v,r) = pair
  (v,discard_value(T,r))

def Vec.set(-T: Data, v: Vec<T>, index: U32, value: T) -> Vec<T> & Result<Error,Unit>:
  set_result(T,Vec.swap(T,v,index,value))

# This plan is bounded by 24 doublings; caller checks minimum <= maximum.
def plan_step(fuel: Nat, +cap: U32, depth: Nat, +minimum: U32, enough: Bool) -> U32 & Nat:
  match fuel:
    case 0n:
      (cap,depth)
    case 1n+p:
      match enough:
        case True{}:
          (cap,depth)
        case False{}:
          +next = U32.add(cap,cap)
          plan_step(p,next,1n+depth,minimum,U32.is_le(minimum,next))

def unpack(-A: Type, -B: Type, -R: Type, pair: A & B, f: A -> B -> R) -> R:
  (a,b) = pair
  f(a,b)

def copy_slots(-T: Data, count: Nat, +i: U32,
  old: Array<Maybe<&2,T>>, fresh: Array<Maybe<&2,T>>) -> Array<Maybe<&2,T>>:
  match count:
    case 0n:
      fresh
    case 1n+p:
      unpack(Array<Maybe<&2,T>>,Maybe<&2,T>,Array<Maybe<&2,T>>,
        Array.get(Maybe<&2,T>,old,i),
        a => x => copy_slots(T,p,U32.add(i,1),a,Array.set(Maybe<&2,T>,fresh,i,x)))

def allocate(-T: Data, +n: U32, m: U32, a: Array<Maybe<&2,T>>, plan: U32 & Nat) -> Vec<T> & Result<Error,Unit>:
  (cap,+depth) = plan
  fresh = Array.new(Maybe<&2,T>,depth,None{})
  slots = copy_slots(T,U32.to_nat(n),0,a,fresh)
  (Buffer{n,cap,depth,m,slots},Done{Unit{}})

def reserve_grow(-T: Data, +n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, +minimum: U32, enough: Bool) -> Vec<T> & Result<Error,Unit>:
  match enough:
    case True{}:
      (Buffer{n,c,d,m,a},Done{Unit{}})
    case False{}:
      allocate(T,n,m,a,plan_step(24n,1,0n,minimum,U32.is_le(minimum,1)))

def reserve_limit(-T: Data, n: U32, +c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, +minimum: U32, valid: Bool) -> Vec<T> & Result<Error,Unit>:
  match valid:
    case False{}:
      (Buffer{n,c,d,m,a},Fail{Limit{}})
    case True{}:
      reserve_grow(T,n,c,d,m,a,minimum,U32.is_le(minimum,c))

def Vec.reserve(-T: Data, v: Vec<T>, +minimum: U32) -> Vec<T> & Result<Error,Unit>:
  match v:
    case Buffer{n,c,d,+m,a}:
      reserve_limit(T,n,c,d,m,a,minimum,U32.is_le(minimum,m))

def push_ready(-T: Data, v: Vec<T>, value: T, r: Result<Error,Unit>) -> Vec<T> & Result<Error,Unit>:
  match v:
    case Buffer{+n,c,d,m,a}:
      match r:
        case Fail{e}:
          (Buffer{n,c,d,m,a},Fail{e})
        case Done{u}:
          (Buffer{U32.add(n,1),c,d,m,Array.set(Maybe<&2,T>,a,n,Some{value})},Done{Unit{}})

def push_reserved(-T: Data, value: T, pair: Vec<T> & Result<Error,Unit>) -> Vec<T> & Result<Error,Unit>:
  (v,r) = pair
  push_ready(T,v,value,r)

def push_if(-T: Data, +n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, value: T, valid: Bool) -> Vec<T> & Result<Error,Unit>:
  match valid:
    case False{}:
      (Buffer{n,c,d,m,a},Fail{Limit{}})
    case True{}:
      push_reserved(T,value,Vec.reserve(T,Buffer{n,c,d,m,a},U32.add(n,1)))

def Vec.push(-T: Data, v: Vec<T>, value: T) -> Vec<T> & Result<Error,Unit>:
  match v:
    case Buffer{+n,c,d,+m,a}:
      push_if(T,n,c,d,m,a,value,U32.is_lt(n,m))

def pop_if(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, empty: Bool) -> Vec<T> & Result<Error,T>:
  match empty:
    case True{}:
      (Buffer{n,c,d,m,a},Fail{Empty{}})
    case False{}:
      +last = U32.sub(n,1)
      observed(T,last,c,d,m,Array.swap(Maybe<&2,T>,a,last,None{}))

def Vec.pop(-T: Data, v: Vec<T>) -> Vec<T> & Result<Error,T>:
  match v:
    case Buffer{+n,c,d,m,a}:
      pop_if(T,n,c,d,m,a,U32.is_eq(n,0))

def prepend_slot(-T: Data, acc: List<T>, x: Maybe<&2,T>) -> List<T>:
  match x:
    case None{}:
      acc
    case Some{v}:
      Con{v,acc}

# Build from the right so the result is ordered without quadratic append.
def collect(-T: Data, count: Nat, last: U32, a: Array<Maybe<&2,T>>,
  acc: List<T>) -> Array<Maybe<&2,T>> & List<T>:
  match count:
    case 0n:
      (a,acc)
    case 1n+p:
      +i = U32.sub(last,1)
      unpack(Array<Maybe<&2,T>>,Maybe<&2,T>,Array<Maybe<&2,T>> & List<T>,
        Array.get(Maybe<&2,T>,a,i),
        b => x => collect(T,p,i,b,prepend_slot(T,acc,x)))

def slice_collected(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  pair: Array<Maybe<&2,T>> & List<T>) -> Vec<T> & Result<Error,List<T>>:
  (a,xs) = pair
  (Buffer{n,c,d,m,a},Done{xs})

def list_collected(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  pair: Array<Maybe<&2,T>> & List<T>) -> Vec<T> & List<T>:
  (a,xs) = pair
  (Buffer{n,c,d,m,a},xs)

def slice_if(-T: Data, n: U32, c: U32, d: Nat, m: U32,
  a: Array<Maybe<&2,T>>, start: U32, +end: U32, valid: Bool) -> Vec<T> & Result<Error,List<T>>:
  match valid:
    case False{}:
      (Buffer{n,c,d,m,a},Fail{InvalidRange{}})
    case True{}:
      slice_collected(T,n,c,d,m,collect(T,U32.to_nat(U32.sub(end,start)),end,a,Nil{}))

def Vec.slice(-T: Data, v: Vec<T>, +start: U32, +end: U32) -> Vec<T> & Result<Error,List<T>>:
  match v:
    case Buffer{+n,c,d,m,a}:
      slice_if(T,n,c,d,m,a,start,end,Bool.and(U32.is_le(start,end),U32.is_le(end,n)))

def Vec.to_list(-T: Data, v: Vec<T>) -> Vec<T> & List<T>:
  match v:
    case Buffer{+n,c,d,m,a}:
      list_collected(T,n,c,d,m,collect(T,U32.to_nat(n),n,a,Nil{}))
