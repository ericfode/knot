# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M
import ./LAWS.bend as L

def L.path_empty(V,path):
  match path:
    case Nil{}: {==}
    case Con{False{},+tail}: L.path_empty(V,tail)
    case Con{True{},+tail}: L.path_empty(V,tail)

def L.path_set(V,path,m,key,v):
  match path:
    case Nil{}: {==}
    case Con{False{},+tail}: L.path_set(V,tail,M.low(V,m),key,v)
    case Con{True{},+tail}: L.path_set(V,tail,M.high(V,m),key,v)

def L.branch_low(V,lo,hi):
  match lo:
    case M.Tip{}:
      match hi:
        case M.Tip{}: {==}
        case M.Entry{k,v}: {==}
        case M.Branch{a,b}: {==}
    case M.Entry{k,v}: {==}
    case M.Branch{a,b}: {==}

def L.branch_high(V,lo,hi):
  match lo:
    case M.Tip{}:
      match hi:
        case M.Tip{}: {==}
        case M.Entry{k,v}: {==}
        case M.Branch{a,b}: {==}
    case M.Entry{k,v}: {==}
    case M.Branch{a,b}: {==}

def L.path_remove(V,path,m):
  match path:
    case Nil{}: {==}
    case Con{False{},+tail}:
      %Equal.sym(M.IntMap<V>,M.low(V,M.branch(V,M.remove_path(V,tail,M.low(V,m)),M.high(V,m))),M.remove_path(V,tail,M.low(V,m)),L.branch_low(V,M.remove_path(V,tail,M.low(V,m)),M.high(V,m))) : {M.get_path(V,tail,_) == None{} : Maybe<&2,V>}
      L.path_remove(V,tail,M.low(V,m))
    case Con{True{},+tail}:
      %Equal.sym(M.IntMap<V>,M.high(V,M.branch(V,M.low(V,m),M.remove_path(V,tail,M.high(V,m)))),M.remove_path(V,tail,M.high(V,m)),L.branch_high(V,M.low(V,m),M.remove_path(V,tail,M.high(V,m)))) : {M.get_path(V,tail,_) == None{} : Maybe<&2,V>}
      L.path_remove(V,tail,M.high(V,m))

def L.empty_get(V,key): L.path_empty(V,M.bits(32n,key))
def L.set_get(V,m,key,v): L.path_set(V,M.bits(32n,key),m,key,v)
def L.remove_get(V,m,key): L.path_remove(V,M.bits(32n,key),m)

def L.set_contains(V,m,key,v):
  %Equal.sym(Maybe<&2,V>,M.IntMap.get(V,M.IntMap.set(V,m,key,v),key),Some{v},L.set_get(V,m,key,v)) : {M.present(V,_) == True{} : Bool}
  {==}

def L.overwrite(V,m,key,old,v):
  L.set_get(V,M.IntMap.set(V,m,key,old),key,v)

def L.path_preserve(V,p,q,m,key,v,distinct):
  match p:
    case Nil{}:
      match distinct:
    case Con{False{},pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},qt}: L.path_preserve(V,pt,qt,M.low(V,m),key,v,distinct)
        case Con{True{},qt}: {==}
    case Con{True{},pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},qt}: {==}
        case Con{True{},qt}: L.path_preserve(V,pt,qt,M.high(V,m),key,v,distinct)

def L.set_preserves(V,m,key,other,v,distinct):
  L.path_preserve(V,M.bits(32n,key),M.bits(32n,other),m,key,v,distinct)

def L.distinct_witness(): Unit{}

def L.boundary_fixture(): {==}

def L.fold_fixture(): {==}

def L.union_fixture(): {==}

def L.invocation_fixture(): {==}

def L.model_union_fixture(): {==}

def L.observe_low(V,path,lo,hi):
  Equal.cong(M.IntMap<V>,Maybe<&2,V>,x => M.get_path(V,path,x),M.low(V,M.branch(V,lo,hi)),lo,L.branch_low(V,lo,hi))

def L.observe_high(V,path,lo,hi):
  Equal.cong(M.IntMap<V>,Maybe<&2,V>,x => M.get_path(V,path,x),M.high(V,M.branch(V,lo,hi)),hi,L.branch_high(V,lo,hi))

def L.path_remove_preserve(V,p,q,m,distinct):
  match p:
    case Nil{}:
      match distinct:
    case Con{False{},+pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},+qt}:
          Equal.trans(Maybe<&2,V>,
            M.get_path(V,qt,M.low(V,M.branch(V,M.remove_path(V,pt,M.low(V,m)),M.high(V,m)))),
            M.get_path(V,qt,M.remove_path(V,pt,M.low(V,m))),M.get_path(V,qt,M.low(V,m)),
            L.observe_low(V,qt,M.remove_path(V,pt,M.low(V,m)),M.high(V,m)),
            L.path_remove_preserve(V,pt,qt,M.low(V,m),distinct))
        case Con{True{},qt}:
          L.observe_high(V,qt,M.remove_path(V,pt,M.low(V,m)),M.high(V,m))
    case Con{True{},+pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},qt}:
          L.observe_low(V,qt,M.low(V,m),M.remove_path(V,pt,M.high(V,m)))
        case Con{True{},+qt}:
          Equal.trans(Maybe<&2,V>,
            M.get_path(V,qt,M.high(V,M.branch(V,M.low(V,m),M.remove_path(V,pt,M.high(V,m))))),
            M.get_path(V,qt,M.remove_path(V,pt,M.high(V,m))),M.get_path(V,qt,M.high(V,m)),
            L.observe_high(V,qt,M.low(V,m),M.remove_path(V,pt,M.high(V,m))),
            L.path_remove_preserve(V,pt,qt,M.high(V,m),distinct))

def L.remove_preserves(V,m,key,other,distinct):
  L.path_remove_preserve(V,M.bits(32n,key),M.bits(32n,other),m,distinct)

def L.fold_seed_fixture(): {==}
