# SPDX-License-Identifier: MIT-0
import Base

# Internal constructors: public maps are built through the IntMap operations.
type IntMap<-V: Data> is Data:
  Tip{}
  Entry{key: U32, value: V}
  Branch{lo: IntMap<V>, hi: IntMap<V>}

def bits(n: Nat, +key: U32) -> List<&2,Bool>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      Con{U32.is_ne(U32.and(key,1),0),bits(p,U32.shr(key))}

def low(-V: Data, m: IntMap<V>) -> IntMap<V>:
  match m:
    case Tip{}: Tip{}
    case Entry{k,v}: Tip{}
    case Branch{lo,hi}: lo

def high(-V: Data, m: IntMap<V>) -> IntMap<V>:
  match m:
    case Tip{}: Tip{}
    case Entry{k,v}: Tip{}
    case Branch{lo,hi}: hi

def value(-V: Data, m: IntMap<V>) -> Maybe<&2,V>:
  match m:
    case Tip{}: None{}
    case Entry{k,v}: Some{v}
    case Branch{lo,hi}: None{}

def get_path(-V: Data, path: List<&2,Bool>, m: IntMap<V>) -> Maybe<&2,V>:
  match path:
    case Nil{}:
      value(V,m)
    case Con{False{},tail}:
      get_path(V,tail,low(V,m))
    case Con{True{},tail}:
      get_path(V,tail,high(V,m))

def set_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>, key: U32, v: V) -> IntMap<V>:
  match path:
    case Nil{}:
      Entry{key,v}
    case Con{False{},tail}:
      Branch{set_path(V,tail,low(V,m),key,v),high(V,m)}
    case Con{True{},tail}:
      Branch{low(V,m),set_path(V,tail,high(V,m),key,v)}

def branch(-V: Data, lo: IntMap<V>, hi: IntMap<V>) -> IntMap<V>:
  match lo:
    case Tip{}:
      match hi:
        case Tip{}: Tip{}
        case Entry{k,v}: Branch{Tip{},Entry{k,v}}
        case Branch{a,b}: Branch{Tip{},Branch{a,b}}
    case Entry{k,v}: Branch{Entry{k,v},hi}
    case Branch{a,b}: Branch{Branch{a,b},hi}

def remove_path(-V: Data, path: List<&2,Bool>, +m: IntMap<V>) -> IntMap<V>:
  match path:
    case Nil{}:
      Tip{}
    case Con{False{},tail}:
      branch(V,remove_path(V,tail,low(V,m)),high(V,m))
    case Con{True{},tail}:
      branch(V,low(V,m),remove_path(V,tail,high(V,m)))

def IntMap.empty(-V: Data) -> IntMap<V>:
  Tip{}

def IntMap.get(-V: Data, m: IntMap<V>, key: U32) -> Maybe<&2,V>:
  get_path(V,bits(32n,key),m)

def IntMap.set(-V: Data, m: IntMap<V>, +key: U32, v: V) -> IntMap<V>:
  set_path(V,bits(32n,key),m,key,v)

def IntMap.remove(-V: Data, m: IntMap<V>, key: U32) -> IntMap<V>:
  remove_path(V,bits(32n,key),m)

def present(-V: Data, v: Maybe<&2,V>) -> Bool:
  match v:
    case None{}: False{}
    case Some{x}: True{}

def IntMap.contains(-V: Data, m: IntMap<V>, key: U32) -> Bool:
  present(V,IntMap.get(V,m,key))

def IntMap.size(-V: Data, m: IntMap<V>) -> Nat:
  match m:
    case Tip{}: 0n
    case Entry{k,v}: 1n
    case Branch{lo,hi}: Nat.add(IntMap.size(V,lo),IntMap.size(V,hi))

def IntMap.fold(~V: Data, ~A: Type, ~step: A -> U32 -> V -> A, m: IntMap<V>, acc: A) -> A:
  match m:
    case Tip{}: acc
    case Entry{k,v}: step(acc,k,v)
    case Branch{lo,hi}:
      IntMap.fold(~V,~A,~step,hi,IntMap.fold(~V,~A,~step,lo,acc))

def combine_value(~V: Data, ~combine: V -> V -> V, old: Maybe<&2,V>, right: V) -> V:
  match old:
    case None{}: right
    case Some{left}: combine(left,right)

def union_step(~V: Data, ~combine: V -> V -> V, +left: IntMap<V>, +key: U32, right: V) -> IntMap<V>:
  IntMap.set(V,left,key,combine_value(~V,~combine,IntMap.get(V,left,key),right))

def IntMap.union_with(~V: Data, ~combine: V -> V -> V, left: IntMap<V>, right: IntMap<V>) -> IntMap<V>:
  IntMap.fold(~V,~IntMap<V>,~(acc => key => v => union_step(~V,~combine,acc,key,v)),right,left)
