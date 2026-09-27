# SPDX-License-Identifier: MIT-0
import Base
import ../main.bend as M
import ../LAWS.bend as L

# Rebuilding preserves both projections; the endpoint itself is unrestricted.
law edit_here:
  for ~join: @-T: Data -> M.IntMap<T> -> M.IntMap<T> -> M.IntMap<T>
  for ~left: @-T: Data -> @+a: M.IntMap<T> -> @+b: M.IntMap<T> -> {M.low(T,join(T,a,b)) == a : M.IntMap<T>}
  for ~right: @-T: Data -> @+a: M.IntMap<T> -> @+b: M.IntMap<T> -> {M.high(T,join(T,a,b)) == b : M.IntMap<T>}
  for -V: Data
  for +path: List<&2,Bool>
  for +m: M.IntMap<V>
  for +end: M.IntMap<V>
  {M.get_path(V,path,M.edit_path(~join,V,path,m,end)) == M.value(V,end) : Maybe<&2,V>}

# A first differing bit separates the edited spine from the observed subtree.
law edit_away:
  for ~join: @-T: Data -> M.IntMap<T> -> M.IntMap<T> -> M.IntMap<T>
  for ~left: @-T: Data -> @+a: M.IntMap<T> -> @+b: M.IntMap<T> -> {M.low(T,join(T,a,b)) == a : M.IntMap<T>}
  for ~right: @-T: Data -> @+a: M.IntMap<T> -> @+b: M.IntMap<T> -> {M.high(T,join(T,a,b)) == b : M.IntMap<T>}
  for -V: Data
  for +p: List<&2,Bool>
  for +q: List<&2,Bool>
  for +m: M.IntMap<V>
  for +end: M.IntMap<V>
  for distinct: L.separated(p,q)
  {M.get_path(V,q,M.edit_path(~join,V,p,m,end)) == M.get_path(V,q,m) : Maybe<&2,V>}

# Raw Branch projects by reduction. Pruning uses L.branch_low/L.branch_high.
law raw_low:
  for -V: Data
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.low(V,M.Branch{lo,hi}) == lo : M.IntMap<V>}

law raw_high:
  for -V: Data
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.high(V,M.Branch{lo,hi}) == hi : M.IntMap<V>}

# The original public propositions, now derived from the shared recurrence.
law set_get:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +v: V
  {M.IntMap.get(V,M.IntMap.set(V,m,key,v),key) == Some{v} : Maybe<&2,V>}

law remove_get:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  {M.IntMap.get(V,M.IntMap.remove(V,m,key),key) == None{} : Maybe<&2,V>}

law set_preserves:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +other: U32
  for +v: V
  for distinct: L.separated(M.bits(32n,key),M.bits(32n,other))
  {M.IntMap.get(V,M.IntMap.set(V,m,key,v),other) == M.IntMap.get(V,m,other) : Maybe<&2,V>}

law remove_preserves:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +other: U32
  for distinct: L.separated(M.bits(32n,key),M.bits(32n,other))
  {M.IntMap.get(V,M.IntMap.remove(V,m,key),other) == M.IntMap.get(V,m,other) : Maybe<&2,V>}
