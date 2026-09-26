# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M
import ./model.bend as Ref

def maybe_eq(a: Maybe<&2,U32>, b: Maybe<&2,U32>) -> Bool:
  match a:
    case None{}:
      match b:
        case None{}: True{}
        case Some{x}: False{}
    case Some{x}:
      match b:
        case None{}: False{}
        case Some{y}: U32.is_eq(x,y)

def items_eq(a: List<&2,Ref.Item<U32>>, b: List<&2,Ref.Item<U32>>) -> Bool:
  match a:
    case Nil{}:
      match b:
        case Nil{}: True{}
        case Con{x,xs}: False{}
    case Con{Ref.Item{k,v},xs}:
      match b:
        case Nil{}: False{}
        case Con{Ref.Item{j,w},ys}: Bool.and(U32.is_eq(k,j),Bool.and(U32.is_eq(v,w),items_eq(xs,ys)))

def entries(m: M.IntMap<U32>) -> List<&2,Ref.Item<U32>>:
  List.reverse(&2,Ref.Item<U32>,M.IntMap.fold(~U32,~List<&2,Ref.Item<U32>>,~(acc => k => v => Con{Ref.Item{k,v},acc}),m,Nil{}))

def probes(xs: List<&2,Ref.Item<U32>>, +m: M.IntMap<U32>, +model: List<&2,Ref.Item<U32>>) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{Ref.Item{+k,v},tail}:
      Bool.and(maybe_eq(M.IntMap.get(U32,m,k),Ref.get(U32,model,k)),probes(tail,m,model))

def agree(+m: M.IntMap<U32>, +model: List<&2,Ref.Item<U32>>) -> Bool:
  Bool.and(Nat.is_eq(M.IntMap.size(U32,m),Ref.size(U32,model)),
    Bool.and(probes(model,m,model),Bool.and(probes(entries(m),m,model),
      Nat.is_eq(Ref.size(U32,entries(m)),Ref.size(U32,model)))))

def boundary() -> Bool:
  +a = M.IntMap.set(U32,M.IntMap.empty(U32),0,0)
  +b = M.IntMap.set(U32,a,4294967295,99)
  +c = M.IntMap.set(U32,b,0,17)
  +d = M.IntMap.remove(U32,c,4294967295)
  +e = M.IntMap.remove(U32,d,0)
  Bool.and(maybe_eq(M.IntMap.get(U32,a,0),Some{0}),
  Bool.and(M.IntMap.contains(U32,a,0),
  Bool.and(Bool.not(M.IntMap.contains(U32,a,1)),
  Bool.and(agree(b,[Ref.Item{0,0},Ref.Item{4294967295,99}]),
  Bool.and(agree(c,[Ref.Item{0,17},Ref.Item{4294967295,99}]),
  Bool.and(agree(d,[Ref.Item{0,17}]),
  Bool.and(agree(e,Nil{}),agree(M.IntMap.remove(U32,b,2147483648),[Ref.Item{0,0},Ref.Item{4294967295,99}]))))))))

def bit_cases(n: Nat, +key: U32) -> Bool:
  match n:
    case 0n: True{}
    case 1n+p:
      +complement = U32.not(key)
      +m = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),0,7),key,23),complement,41)
      Bool.and(agree(m,[Ref.Item{0,7},Ref.Item{key,23},Ref.Item{complement,41}]),
        Bool.and(agree(M.IntMap.remove(U32,m,key),[Ref.Item{0,7},Ref.Item{complement,41}]),bit_cases(p,U32.shl(key))))

def order_case() -> Bool:
  m = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),1,11),2,22),0,0),2147483648,33)
  items_eq(entries(m),[Ref.Item{0,0},Ref.Item{2147483648,33},Ref.Item{2,22},Ref.Item{1,11}])

def noncomm(a: U32, b: U32) -> U32: U32.add(U32.mul(a,100),b)

def left() -> M.IntMap<U32>:
  M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),0,2),4294967295,3)

def right() -> M.IntMap<U32>:
  M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),1,5),4294967295,7)

def unions() -> Bool:
  +l = left()
  +r = right()
  Bool.and(agree(M.IntMap.union_with(~U32,~noncomm,l,r),[Ref.Item{0,2},Ref.Item{1,5},Ref.Item{4294967295,307}]),
  Bool.and(agree(M.IntMap.union_with(~U32,~U32.add,l,r),[Ref.Item{0,2},Ref.Item{1,5},Ref.Item{4294967295,10}]),
  Bool.and(agree(M.IntMap.union_with(~U32,~(a => b => U32.max(a,b)),l,r),[Ref.Item{0,2},Ref.Item{1,5},Ref.Item{4294967295,7}]),
  Bool.and(agree(M.IntMap.union_with(~U32,~noncomm,M.IntMap.empty(U32),r),[Ref.Item{1,5},Ref.Item{4294967295,7}]),
  Bool.and(agree(M.IntMap.union_with(~U32,~noncomm,l,M.IntMap.empty(U32)),[Ref.Item{0,2},Ref.Item{4294967295,3}]),
  Bool.and(agree(l,[Ref.Item{0,2},Ref.Item{4294967295,3}]),agree(r,[Ref.Item{1,5},Ref.Item{4294967295,7}])))))))

# A combiner result records its complete invocation tree, including order.
type Trace is Data:
  Atom{value: U32}
  Join{left: Trace, right: Trace}

def join(a: Trace, b: Trace) -> Trace: Join{a,b}

def trace_result(a: Maybe<&2,Trace>, b: Maybe<&2,Trace>, c: Maybe<&2,Trace>) -> Bool:
  match a:
    case None{}: False{}
    case Some{x}:
      match x:
        case Atom{v}: False{}
        case Join{Atom{l},Atom{r}}:
          match b:
            case None{}: False{}
            case Some{Atom{b}}:
              match c:
                case None{}: False{}
                case Some{Atom{c}}: Bool.and(U32.is_eq(l,2),Bool.and(U32.is_eq(r,7),Bool.and(U32.is_eq(b,11),U32.is_eq(c,13))))
                case Some{Join{x,y}}: False{}
            case Some{Join{x,y}}: False{}
        case Join{Atom{l},Join{a,b}}: False{}
        case Join{Join{a,b},r}: False{}

def trace_case() -> Bool:
  l = M.IntMap.set(Trace,M.IntMap.set(Trace,M.IntMap.empty(Trace),9,Atom{2}),10,Atom{11})
  r = M.IntMap.set(Trace,M.IntMap.set(Trace,M.IntMap.empty(Trace),9,Atom{7}),12,Atom{13})
  +m = M.IntMap.union_with(~Trace,~join,l,r)
  trace_result(M.IntMap.get(Trace,m,9),M.IntMap.get(Trace,m,10),M.IntMap.get(Trace,m,12))

def query_domain(n: Nat, +m: M.IntMap<U32>, +model: List<&2,Ref.Item<U32>>) -> Bool:
  match n:
    case 0n: True{}
    case 1n+ +p:
      +k = U32.from_nat(p)
      Bool.and(maybe_eq(M.IntMap.get(U32,m,k),Ref.get(U32,model,k)),
        Bool.and(Bool.not(Bool.xor(M.IntMap.contains(U32,m,k),M.present(U32,Ref.get(U32,model,k)))),query_domain(p,m,model)))

def sequence(n: Nat, +seed: U32, +m: M.IntMap<U32>, +model: List<&2,Ref.Item<U32>>) -> Bool:
  match n:
    case 0n: Bool.and(agree(m,model),query_domain(64n,m,model))
    case 1n+ +p:
      +key = U32.and(seed,63)
      +next = U32.add(U32.mul(seed,1664525),1013904223)
      +changed = M.IntMap.set(U32,m,key,seed)
      +expected = Ref.set(U32,model,key,seed)
      +removed = M.IntMap.remove(U32,changed,U32.and(U32.shr(seed),63))
      +removed_model = Ref.remove(U32,expected,U32.and(U32.shr(seed),63))
      Bool.and(query_domain(64n,changed,expected),Bool.and(query_domain(64n,removed,removed_model),Bool.and(agree(m,model),Bool.and(agree(changed,expected),Bool.and(agree(removed,removed_model),sequence(p,next,removed,removed_model))))))

def union_model() -> Bool:
  +l = {[Ref.Item{0,2},Ref.Item{4294967295,3}] : List<&2,Ref.Item<U32>>}
  +r = {[Ref.Item{1,5},Ref.Item{4294967295,7}] : List<&2,Ref.Item<U32>>}
  agree(M.IntMap.union_with(~U32,~noncomm,left(),right()),Ref.union_with(~U32,~noncomm,r,l))

def fill(n: Nat, +seed: U32, m: M.IntMap<U32>, xs: List<&2,Ref.Item<U32>>) -> M.IntMap<U32> & List<&2,Ref.Item<U32>>:
  match n:
    case 0n: (m,xs)
    case 1n+p:
      +key = U32.and(seed,127)
      fill(p,U32.add(U32.mul(seed,1664525),1013904223),M.IntMap.set(U32,m,key,seed),Ref.set(U32,xs,key,seed))

def union_stress_check(+a: M.IntMap<U32>, +x: List<&2,Ref.Item<U32>>, +b: M.IntMap<U32>, +y: List<&2,Ref.Item<U32>>) -> Bool:
  Bool.and(agree(M.IntMap.union_with(~U32,~noncomm,a,b),Ref.union_with(~U32,~noncomm,y,x)),
    Bool.and(agree(M.IntMap.union_with(~U32,~U32.add,a,b),Ref.union_with(~U32,~U32.add,y,x)),
      Bool.and(agree(M.IntMap.union_with(~U32,~(a => b => U32.max(a,b)),a,b),Ref.union_with(~U32,~(a => b => U32.max(a,b)),y,x)),
        Bool.and(agree(a,x),agree(b,y)))))

def union_stress_pairs(a: M.IntMap<U32> & List<&2,Ref.Item<U32>>, b: M.IntMap<U32> & List<&2,Ref.Item<U32>>) -> Bool:
  match a:
    case Tuple{am,ax}:
      match b:
        case Tuple{bm,bx}: union_stress_check(am,ax,bm,bx)

def union_stress() -> Bool:
  union_stress_pairs(fill(96n,731,M.IntMap.empty(U32),Nil{}),fill(96n,9923,M.IntMap.empty(U32),Nil{}))

def fold_seed_case() -> Bool:
  +m = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),0,7),1,11),2,22)
  +seed = {[Ref.Item{99,123}] : List<&2,Ref.Item<U32>>}
  Bool.and(items_eq(M.IntMap.fold(~U32,~List<&2,Ref.Item<U32>>,~(acc => k => v => Con{Ref.Item{k,v},acc}),m,seed),
    [Ref.Item{1,11},Ref.Item{2,22},Ref.Item{0,7},Ref.Item{99,123}]),
    items_eq(M.IntMap.fold(~U32,~List<&2,Ref.Item<U32>>,~(acc => k => v => Con{Ref.Item{k,v},acc}),M.IntMap.empty(U32),seed),seed))
