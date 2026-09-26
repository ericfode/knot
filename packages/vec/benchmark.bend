import Base
import ./main.bend as V

type Counts is Data:
  Counts{growths: U32, copied: U32, initialized: U32}

type Report is Data:
  Report{n: U32, capacity: U32, growths: U32, copied: U32, initialized: U32, checksum: U32, valid: Bool}

def count_growth(old: U32, new: U32, used: U32, counts: Counts, grew: Bool) -> Counts:
  match counts:
    case Counts{g,c,a}:
      match grew:
        case False{}: Counts{g,c,a}
        case True{}: Counts{U32.add(g,1),U32.add(c,used),U32.add(a,new)}

def pushed(used: U32, +old: U32, counts: Counts, pair: V.Vec<U32> & U32) -> V.Vec<U32> & Counts:
  (v,+c) = pair
  (v,count_growth(old,c,used,counts,U32.is_lt(old,c)))

def pushed_result(used: U32, old: U32, counts: Counts, pair: V.Vec<U32> & Result<V.Error,Unit>) -> V.Vec<U32> & Counts:
  (v,r) = pair
  pushed(used,old,counts,V.Vec.capacity(U32,v))

def push_one(+i: U32, counts: Counts, pair: V.Vec<U32> & U32) -> V.Vec<U32> & Counts:
  (v,c) = pair
  pushed_result(i,c,counts,V.Vec.push(U32,v,U32.add(U32.mul(i,17),3)))

def build(n: Nat, +i: U32, state: V.Vec<U32> & Counts) -> V.Vec<U32> & Counts:
  match n:
    case 0n: state
    case 1n+p:
      (v,c) = state
      build(p,U32.add(i,1),push_one(i,c,V.Vec.capacity(U32,v)))

def check_result(expected: U32, sum: U32, ok: Bool, r: Result<V.Error,U32>) -> U32 & Bool:
  match r:
    case Fail{e}: (sum,False{})
    case Done{+x}: (U32.add(sum,x),Bool.and(ok,U32.is_eq(expected,x)))

def checked(expected: U32, sum: U32, ok: Bool, pair: V.Vec<U32> & Result<V.Error,U32>) -> V.Vec<U32> & (U32 & Bool):
  (v,r) = pair
  (v,check_result(expected,sum,ok,r))

def verify(n: Nat, +i: U32, state: V.Vec<U32> & (U32 & Bool)) -> V.Vec<U32> & (U32 & Bool):
  match n:
    case 0n: state
    case 1n+p:
      (v,(sum,ok)) = state
      verify(p,U32.add(i,1),checked(U32.add(U32.mul(i,17),3),sum,ok,V.Vec.get(U32,v,i)))

def report(n: U32, counts: Counts, sum: U32, ok: Bool, pair: V.Vec<U32> & U32) -> Report:
  match counts:
    case Counts{g,c,a}:
      (v,capacity) = pair
      Report{n,capacity,g,c,a,sum,ok}

def verified(n: U32, counts: Counts, pair: V.Vec<U32> & (U32 & Bool)) -> Report:
  (v,(sum,ok)) = pair
  report(n,counts,sum,ok,V.Vec.capacity(U32,v))

def built(+n: Nat, pair: V.Vec<U32> & Counts) -> Report:
  (v,c) = pair
  verified(U32.from_nat(n),c,verify(n,0,(v,(0,True{}))))

def workload(+n: Nat) -> Report:
  built(n,build(n,0,(V.Vec.new(U32),Counts{0,0,1})))
