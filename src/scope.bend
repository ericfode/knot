import Base
import ./syntax.bend as S
import ./core.bend as C
import ./descent.bend as D

type Scope is Data:
  Scope{bindings: List<&2,C.Binding>, next_level: U32, open: List<&2,U32>, live: Bool, aliases: List<&2,D.Alias>}

def contains(ids: List<&2,U32>, +id: U32) -> Bool:
  match ids:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(U32.is_eq(h,id),contains(t,id))

# Only live affine occurrences enter these sets. Sequential sets must be
# disjoint; alternatives take their union. No machine counter can wrap.
def sequential(xs: List<&2,U32>, +ys: List<&2,U32>, +token: S.Token) -> Result<S.Error,List<&2,U32>>:
  match xs:
    case Nil{}: Done{ys}
    case Con{+h,+t}:
      S.choose(Result<S.Error,List<&2,U32>>,contains(ys,h),u => C.invalid(List<&2,U32>,"affine-reuse",token),u =>
        S.bind(List<&2,U32>,List<&2,U32>,sequential(t,ys,token),rest => Done{Con{h,rest}}))

def alternatives(xs: List<&2,U32>, +ys: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: ys
    case Con{+h,t}: alternatives(t,S.choose(List<&2,U32>,contains(ys,h),u => ys,u => Con{h,ys}))

def remove(ids: List<&2,U32>, +id: U32) -> List<&2,U32>:
  match ids:
    case Nil{}: Nil{}
    case Con{+h,+t}:
      S.choose(List<&2,U32>,U32.is_eq(h,id),u => remove(t,id),u => Con{h,remove(t,id)})

def find(bindings: List<&2,C.Binding>, +name: S.Token) -> Result<S.Error,C.Binding>:
  match bindings:
    case Nil{}: C.invalid(C.Binding,"free-name",name)
    case Con{+head,+tail}:
      match head:
        case C.Binding{token,level,q,type_id,param,known}:
          S.choose(Result<S.Error,C.Binding>,String.eq(S.text(token),S.text(name)),u => Done{head},u => find(tail,name))

def lookup(scope: Scope, +name: S.Token) -> Result<S.Error,C.Binding>:
  match scope:
    case Scope{bindings,level,from,live,aliases}:
      S.choose(Result<S.Error,C.Binding>,S.matches(name,"_"),u => C.invalid(C.Binding,"free-name",name),u => find(bindings,name))

def occurrence(known: Maybe<&2,C.Term>, +token: S.Token, +level: U32, +q: U32, +type_id: U32, +live: Bool) -> Result<S.Error,C.Checked>:
  match known:
    case Some{C.Value{origin,source_type,tag}}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case Some{other}: C.internal(C.Checked,"compound-refinement")
    case None{}:
      S.choose(Result<S.Error,C.Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(C.Checked,"erased-live",token),u =>
        Done{C.Checked{C.Reference{token,level,type_id},type_id,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})

def reference(binding: C.Binding, token: S.Token, scope: Scope) -> Result<S.Error,C.Checked>:
  match binding scope:
    case C.Binding{name,level,q,type_id,param,known} Scope{bindings,next,from,live,aliases}:
      occurrence(known,token,level,q,type_id,live)

def live_scope(scope: Scope, q: U32) -> Scope:
  match scope:
    case Scope{bindings,next,from,live,aliases}: Scope{bindings,next,from,Bool.and(live,U32.is_ne(q,0)),aliases}

def extend(scope: Scope, token: S.Token, q: U32, type_id: U32, value: C.Term) -> Scope:
  match scope:
    case Scope{bindings,+next,from,live,aliases}:
      Scope{Con{C.Binding{token,next,q,type_id,False{},None{}},bindings},U32.add(next,1),Nil{},live,Con{D.Alias{next,value},aliases}}

def set_known(~A: Data, ~value: A -> S.Token -> U32 -> C.Term, bindings: List<&2,C.Binding>, +level: U32, +payload: A) -> List<&2,C.Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{+token,+id,q,+type_id,param,+known},tail}:
      Con{C.Binding{token,id,q,type_id,param,
        S.choose(Maybe<&2,C.Term>,U32.is_eq(id,level),u => Some{value(payload,token,type_id)},u => known)},
        set_known(~A,~value,tail,level,payload)}

def refine(bindings: List<&2,C.Binding>, +level: U32, +tag: U32) -> List<&2,C.Binding>:
  set_known(~U32,~(tag => token => type_id => C.Value{token,type_id,tag}),bindings,level,tag)

# Lexical identity is stable; match order is an independent ordered frontier.
def after(ids: List<&2,U32>, +level: U32) -> List<&2,U32>:
  match ids:
    case Nil{}: Nil{}
    case Con{head,+tail}:
      S.choose(List<&2,U32>,U32.is_eq(head,level),u => tail,u => after(tail,level))

def levels(bindings: List<&2,C.Binding>) -> List<&2,U32>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,level,q,type_id,param,known},tail}: Con{level,levels(tail)}

def find_level(bindings: List<&2,C.Binding>, +level: U32) -> Result<S.Error,C.Binding>:
  match bindings:
    case Nil{}: C.internal(C.Binding,"binding-level")
    case Con{+head,+tail}:
      match head:
        case C.Binding{token,id,q,type_id,param,known}:
          S.choose(Result<S.Error,C.Binding>,U32.is_eq(id,level),u => Done{head},u => find_level(tail,level))

def replace(bindings: List<&2,C.Binding>, +level: U32, +term: C.Term) -> List<&2,C.Binding>:
  set_known(~C.Term,~(term => token => type_id => term),bindings,level,term)

def remove_fields(fields: List<&2,C.Binding>, uses: List<&2,U32>) -> List<&2,U32>:
  match fields:
    case Nil{}: uses
    case Con{C.Binding{token,id,q,type_id,param,known},tail}: remove_fields(tail,remove(uses,id))

def branch(scope: Scope, +level: U32, tag: U32) -> Scope:
  match scope:
    case Scope{bindings,next,from,live,aliases}: Scope{refine(bindings,level,tag),next,after(from,level),live,aliases}

def parameters(params: List<&2,C.Parameter>, +index: U32, +bindings: List<&2,C.Binding>) -> Scope:
  match params:
    case Nil{}: Scope{bindings,index,List.reverse(&2,U32,levels(bindings)),True{},Nil{}}
    case Con{C.Parameter{token,q,type_id},tail}:
      parameters(tail,U32.add(index,1),Con{C.Binding{token,index,q,type_id,True{},None{}},bindings})

def matchable(binding: C.Binding, +token: S.Token, scope: Scope) -> Result<S.Error,C.Binding>:
  match binding scope:
    case C.Binding{+name,+level,+q,+type_id,+param,None{}} Scope{bindings,next,from,live,aliases}:
      S.choose(Result<S.Error,C.Binding>,U32.is_eq(q,0),u => C.invalid(C.Binding,"erased-scrutinee",token),u =>
        S.choose(Result<S.Error,C.Binding>,Bool.and(param,contains(from,level)),u =>
          Done{C.Binding{name,level,q,type_id,param,None{}}},u => C.invalid(C.Binding,"unmatchable-binder",token)))
    case _ _: C.invalid(C.Binding,"already-matched",token)

def scrutinee(node: S.Node, +scope: Scope) -> Result<S.Error,C.Binding>:
  match node:
    case S.Variable{+token}:
      S.bind(C.Binding,C.Binding,lookup(scope,token),binding => matchable(binding,token,scope))
    case S.Constructor{token,args}: C.invalid(C.Binding,"constructor-scrutinee",token)
    case S.Call{token,args}: C.invalid(C.Binding,"computed-scrutinee",token)
    case _: C.internal(C.Binding,"scrutinee-node")
