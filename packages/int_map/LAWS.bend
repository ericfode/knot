# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M
import ./fixtures.bend as F

# Universal structural path theorems; these have no preconditions.
law path_empty:
  for -V: Data
  for +path: List<&2,Bool>
  {M.get_path(V,path,M.Tip{}) == None{} : Maybe<&2,V>}

law path_set:
  for -V: Data
  for +path: List<&2,Bool>
  for +m: M.IntMap<V>
  for +key: U32
  for +v: V
  {M.get_path(V,path,M.set_path(V,path,m,key,v)) == Some{v} : Maybe<&2,V>}

# Auxiliary projection lemmas for pruning; not behavior claims on their own.
law branch_low:
  for -V: Data
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.low(V,M.branch(V,lo,hi)) == lo : M.IntMap<V>}

law branch_high:
  for -V: Data
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.high(V,M.branch(V,lo,hi)) == hi : M.IntMap<V>}

law path_remove:
  for -V: Data
  for +path: List<&2,Bool>
  for +m: M.IntMap<V>
  {M.get_path(V,path,M.remove_path(V,path,m)) == None{} : Maybe<&2,V>}

# Public universal theorems quantify over every U32, value, and map.
law empty_get:
  for -V: Data
  for +key: U32
  {M.IntMap.get(V,M.IntMap.empty(V),key) == None{} : Maybe<&2,V>}

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

law set_contains:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +v: V
  {M.IntMap.contains(V,M.IntMap.set(V,m,key,v),key) == True{} : Bool}

law overwrite:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +old: V
  for +v: V
  {M.IntMap.get(V,M.IntMap.set(V,M.IntMap.set(V,m,key,old),key,v),key) == Some{v} : Maybe<&2,V>}

# Constructive domain: Unit at first differing bit, Empty for prefix/equal paths.
def separated(p: List<&2,Bool>, q: List<&2,Bool>) -> Data:
  match p:
    case Nil{}: Empty
    case Con{False{},pt}:
      match q:
        case Nil{}: Empty
        case Con{False{},qt}: separated(pt,qt)
        case Con{True{},qt}: Unit
    case Con{True{},pt}:
      match q:
        case Nil{}: Empty
        case Con{False{},qt}: Unit
        case Con{True{},qt}: separated(pt,qt)

law path_preserve:
  for -V: Data
  for +p: List<&2,Bool>
  for +q: List<&2,Bool>
  for +m: M.IntMap<V>
  for +key: U32
  for +v: V
  for distinct: separated(p,q)
  {M.get_path(V,q,M.set_path(V,p,m,key,v)) == M.get_path(V,q,m) : Maybe<&2,V>}

law set_preserves:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +other: U32
  for +v: V
  for distinct: separated(M.bits(32n,key),M.bits(32n,other))
  {M.IntMap.get(V,M.IntMap.set(V,m,key,v),other) == M.IntMap.get(V,m,other) : Maybe<&2,V>}

law distinct_witness:
  separated(M.bits(32n,0),M.bits(32n,2147483648))

# Concrete normalization witness, not a universally quantified theorem.
law boundary_fixture:
  {F.boundary() == True{} : Bool}

# Concrete normalization witness, not a universally quantified theorem.
law fold_fixture:
  {F.order_case() == True{} : Bool}

# Concrete normalization witness, not a universally quantified theorem.
law union_fixture:
  {F.unions() == True{} : Bool}

# Concrete normalization witness, not a universally quantified theorem.
law invocation_fixture:
  {F.trace_case() == True{} : Bool}

# Concrete normalization witness, not a universally quantified theorem.
law model_union_fixture:
  {F.union_model() == True{} : Bool}

# Auxiliary observation lemmas for pruned branches.
law observe_low:
  for -V: Data
  for +path: List<&2,Bool>
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.get_path(V,path,M.low(V,M.branch(V,lo,hi))) == M.get_path(V,path,lo) : Maybe<&2,V>}

law observe_high:
  for -V: Data
  for +path: List<&2,Bool>
  for +lo: M.IntMap<V>
  for +hi: M.IntMap<V>
  {M.get_path(V,path,M.high(V,M.branch(V,lo,hi))) == M.get_path(V,path,hi) : Maybe<&2,V>}

law path_remove_preserve:
  for -V: Data
  for +p: List<&2,Bool>
  for +q: List<&2,Bool>
  for +m: M.IntMap<V>
  for distinct: separated(p,q)
  {M.get_path(V,q,M.remove_path(V,p,m)) == M.get_path(V,q,m) : Maybe<&2,V>}

law remove_preserves:
  for -V: Data
  for +m: M.IntMap<V>
  for +key: U32
  for +other: U32
  for distinct: separated(M.bits(32n,key),M.bits(32n,other))
  {M.IntMap.get(V,M.IntMap.remove(V,m,key),other) == M.IntMap.get(V,m,other) : Maybe<&2,V>}

# Concrete normalization: exact fold contents include the retained seed.
law fold_seed_fixture:
  {F.fold_seed_case() == True{} : Bool}
