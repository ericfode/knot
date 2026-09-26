import Base
import ./syntax.bend as S
import ./core.bend as C

type Scope is Data:
  Scope{bindings: List<&2,C.Binding>, next_level: U32, match_from: U32, live: Bool}

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

def lookup(scope: Scope, name: S.Token) -> Result<S.Error,C.Binding>:
  match scope:
    case Scope{bindings,level,from,live}: find(bindings,name)

def occurrence(known: Maybe<&2,U32>, +token: S.Token, +level: U32, +q: U32, +type_id: U32, +live: Bool) -> Result<S.Error,C.Checked>:
  match known:
    case Some{tag}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case None{}:
      S.choose(Result<S.Error,C.Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(C.Checked,"erased-live",token),u =>
        Done{C.Checked{C.Reference{token,level,type_id},type_id,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})

def reference(binding: C.Binding, token: S.Token, scope: Scope) -> Result<S.Error,C.Checked>:
  match binding scope:
    case C.Binding{name,level,q,type_id,param,known} Scope{bindings,next,from,live}:
      occurrence(known,token,level,q,type_id,live)

def live_scope(scope: Scope, q: U32) -> Scope:
  match scope:
    case Scope{bindings,next,from,live}: Scope{bindings,next,from,Bool.and(live,U32.is_ne(q,0))}

def extend(scope: Scope, token: S.Token, q: U32, type_id: U32) -> Scope:
  match scope:
    case Scope{bindings,+next,from,live}:
      Scope{Con{C.Binding{token,next,q,type_id,False{},None{}},bindings},U32.add(next,1),65536,live}

def refine(bindings: List<&2,C.Binding>, +level: U32, +tag: U32) -> List<&2,C.Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{+token,+id,+q,+type_id,+param,+known},tail}:
      Con{C.Binding{token,id,q,type_id,param,S.choose(Maybe<&2,U32>,U32.is_eq(id,level),u => Some{tag},u => known)},refine(tail,level,tag)}

def branch(scope: Scope, +level: U32, tag: U32) -> Scope:
  match scope:
    case Scope{bindings,next,from,live}: Scope{refine(bindings,level,tag),next,U32.add(level,1),live}

def parameters(params: List<&2,C.Parameter>, +index: U32, bindings: List<&2,C.Binding>) -> Scope:
  match params:
    case Nil{}: Scope{bindings,index,0,True{}}
    case Con{C.Parameter{token,q,type_id},tail}:
      parameters(tail,U32.add(index,1),Con{C.Binding{token,index,q,type_id,True{},None{}},bindings})

def matchable(binding: C.Binding, +token: S.Token, scope: Scope) -> Result<S.Error,C.Binding>:
  match binding scope:
    case C.Binding{+name,+level,+q,+type_id,+param,None{}} Scope{bindings,next,from,live}:
      S.choose(Result<S.Error,C.Binding>,U32.is_eq(q,0),u => C.invalid(C.Binding,"erased-scrutinee",token),u =>
        S.choose(Result<S.Error,C.Binding>,Bool.and(param,U32.is_ge(level,from)),u =>
          Done{C.Binding{name,level,q,type_id,param,None{}}},u => C.invalid(C.Binding,"unmatchable-binder",token)))
    case _ _: C.invalid(C.Binding,"already-matched",token)

def scrutinee(node: S.Node, +scope: Scope) -> Result<S.Error,C.Binding>:
  match node:
    case S.Variable{+token}:
      S.bind(C.Binding,C.Binding,lookup(scope,token),binding => matchable(binding,token,scope))
    case S.Constructor{token,args}: C.invalid(C.Binding,"constructor-scrutinee",token)
    case S.Call{token,args}: C.invalid(C.Binding,"computed-scrutinee",token)
    case _: C.internal(C.Binding,"scrutinee-node")
