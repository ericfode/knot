# SPDX-License-Identifier: MIT-0
import Base

# Independent association list: no trie, key bits, or implementation import.
type Item<-V: Data> is Data:
  Item{key: U32, value: V}

def choose(-V: Data, same: Bool, v: V, rest: Maybe<&2,V>) -> Maybe<&2,V>:
  match same:
    case False{}: rest
    case True{}: Some{v}

def get(-V: Data, xs: List<&2,Item<V>>, +key: U32) -> Maybe<&2,V>:
  match xs:
    case Nil{}: None{}
    case Con{Item{k,v},tail}: choose(V,U32.is_eq(k,key),v,get(V,tail,key))

def keep(-V: Data, same: Bool, x: Item<V>, tail: List<&2,Item<V>>) -> List<&2,Item<V>>:
  match same:
    case False{}: Con{x,tail}
    case True{}: tail

def remove(-V: Data, xs: List<&2,Item<V>>, +key: U32) -> List<&2,Item<V>>:
  match xs:
    case Nil{}: Nil{}
    case Con{Item{+k,v},tail}: keep(V,U32.is_eq(k,key),Item{k,v},remove(V,tail,key))

def set(-V: Data, xs: List<&2,Item<V>>, +key: U32, v: V) -> List<&2,Item<V>>:
  Con{Item{key,v},remove(V,xs,key)}

def size(-V: Data, xs: List<&2,Item<V>>) -> Nat:
  match xs:
    case Nil{}: 0n
    case Con{x,tail}: 1n+size(V,tail)

def merged(~V: Data, ~f: V -> V -> V, old: Maybe<&2,V>, v: V) -> V:
  match old:
    case None{}: v
    case Some{x}: f(x,v)

def union_with(~V: Data, ~f: V -> V -> V, right: List<&2,Item<V>>, +left: List<&2,Item<V>>) -> List<&2,Item<V>>:
  match right:
    case Nil{}: left
    case Con{Item{+k,v},tail}:
      union_with(~V,~f,tail,set(V,left,k,merged(~V,~f,get(V,left,k),v)))
