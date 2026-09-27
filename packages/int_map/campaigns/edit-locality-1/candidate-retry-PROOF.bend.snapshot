# SPDX-License-Identifier: MIT-0
import Base
import ../main.bend as M
import ../LAWS.bend as L
import ../PROOF.bend as Original
import ./LAWS.bend as G

def G.edit_here(join,left,right,V,path,m,end):
  match path:
    case Nil{}: {==}
    case Con{False{},+tail}:
      +edited = M.edit_path(~join,V,tail,M.low(V,m),end)
      %Equal.sym(M.IntMap<V>,M.low(V,join(V,edited,M.high(V,m))),edited,
        left(V,edited,M.high(V,m))) : {M.get_path(V,tail,_) == M.value(V,end) : Maybe<&2,V>}
      G.edit_here(~join,~left,~right,V,tail,M.low(V,m),end)
    case Con{True{},+tail}:
      +edited = M.edit_path(~join,V,tail,M.high(V,m),end)
      %Equal.sym(M.IntMap<V>,M.high(V,join(V,M.low(V,m),edited)),edited,
        right(V,M.low(V,m),edited)) : {M.get_path(V,tail,_) == M.value(V,end) : Maybe<&2,V>}
      G.edit_here(~join,~left,~right,V,tail,M.high(V,m),end)

def G.edit_away(join,left,right,V,p,q,m,end,distinct):
  match p:
    case Nil{}:
      match distinct:
    case Con{False{},+pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},+qt}:
          +edited = M.edit_path(~join,V,pt,M.low(V,m),end)
          %Equal.sym(M.IntMap<V>,M.low(V,join(V,edited,M.high(V,m))),edited,
            left(V,edited,M.high(V,m))) : {M.get_path(V,qt,_) == M.get_path(V,qt,M.low(V,m)) : Maybe<&2,V>}
          G.edit_away(~join,~left,~right,V,pt,qt,M.low(V,m),end,distinct)
        case Con{True{},qt}:
          +edited = M.edit_path(~join,V,pt,M.low(V,m),end)
          Equal.cong(M.IntMap<V>,Maybe<&2,V>,x => M.get_path(V,qt,x),
            M.high(V,join(V,edited,M.high(V,m))),M.high(V,m),right(V,edited,M.high(V,m)))
    case Con{True{},+pt}:
      match q:
        case Nil{}:
          match distinct:
        case Con{False{},qt}:
          +edited = M.edit_path(~join,V,pt,M.high(V,m),end)
          Equal.cong(M.IntMap<V>,Maybe<&2,V>,x => M.get_path(V,qt,x),
            M.low(V,join(V,M.low(V,m),edited)),M.low(V,m),left(V,M.low(V,m),edited))
        case Con{True{},+qt}:
          +edited = M.edit_path(~join,V,pt,M.high(V,m),end)
          %Equal.sym(M.IntMap<V>,M.high(V,join(V,M.low(V,m),edited)),edited,
            right(V,M.low(V,m),edited)) : {M.get_path(V,qt,_) == M.get_path(V,qt,M.high(V,m)) : Maybe<&2,V>}
          G.edit_away(~join,~left,~right,V,pt,qt,M.high(V,m),end,distinct)

def G.raw_low(V,lo,hi): {==}
def G.raw_high(V,lo,hi): {==}

def G.set_get(V,m,key,v):
  G.edit_here(~(T => lo => hi => M.Branch{lo,hi}),~G.raw_low,~G.raw_high,
    V,M.bits(32n,key),m,M.Entry{key,v})

def G.remove_get(V,m,key):
  G.edit_here(~M.branch,~L.branch_low,~L.branch_high,V,M.bits(32n,key),m,M.Tip{})

def G.set_preserves(V,m,key,other,v,distinct):
  G.edit_away(~(T => lo => hi => M.Branch{lo,hi}),~G.raw_low,~G.raw_high,
    V,M.bits(32n,key),M.bits(32n,other),m,M.Entry{key,v},distinct)

def G.remove_preserves(V,m,key,other,distinct):
  G.edit_away(~M.branch,~L.branch_low,~L.branch_high,
    V,M.bits(32n,key),M.bits(32n,other),m,M.Tip{},distinct)
