import Base
import ./syntax.bend as S
import ./core.bend as C

type Scope is Data:
  Scope{bindings: List<&2,C.Binding>, next_level: U32, open: List<&2,U32>, live: Bool, smaller: List<&2,U32>}

def contains(ids: List<&2,U32>, +id: U32) -> Bool:
  match ids:
    case Nil{}: False{}
    case Con{h,t}: Bool.or(U32.is_eq(h,id),contains(t,id))

# Strict descendants of parameter 0, independent of the match frontier.
def descendants(+level: U32, +fields: List<&2,U32>, +smaller: List<&2,U32>) -> List<&2,U32>:
  S.choose(List<&2,U32>,Bool.or(U32.is_eq(level,0),contains(smaller,level)),u =>
    List.append(&2,U32,fields,smaller),u => smaller)

def descends(args: List<&2,C.Term>, smaller: List<&2,U32>) -> Bool:
  match args:
    case Con{C.Reference{token,level,type_id},tail}: contains(smaller,level)
    case _: False{}

# A match refines a level; a later occurrence rebuilds it from its fields.
# A reference to a refined level unfolds to one layer of that refinement.
def layer(known: Maybe<&2,C.Term>, +reference: C.Term) -> C.Term:
  match known:
    case Some{C.Value{token,type_id,tag}}: C.Value{token,type_id,tag}
    case Some{C.Construct{token,type_id,tag,params,args}}: C.Construct{token,type_id,tag,params,args}
    case _: reference

def unfold(bindings: List<&2,C.Binding>, +level: U32, +reference: C.Term) -> C.Term:
  match bindings:
    case Nil{}: reference
    case Con{C.Binding{token,id,q,type_id,param,known},tail}:
      S.choose(C.Term,U32.is_eq(id,level),u => layer(known,reference),u => unfold(tail,level,reference))

def unfolded(refs: List<&2,C.Term>, +bindings: List<&2,C.Binding>) -> List<&2,C.Term>:
  match refs:
    case Nil{}: Nil{}
    case Con{C.Reference{token,+level,+type_id},tail}: Con{unfold(bindings,level,C.Reference{token,level,type_id}),unfolded(tail,bindings)}
    case Con{other,tail}: Con{other,unfolded(tail,bindings)}

# Rebuilt terms denote unfolded layers position-wise: a reference its own
# level, a value or constructor the same type and tag, fields in order.
def denotes(terms: List<&2,C.Term>, layers: List<&2,C.Term>, +bindings: List<&2,C.Binding>) -> Bool:
  match terms layers:
    case Nil{} Nil{}: True{}
    case Con{C.Reference{a,id,x},tail} Con{C.Reference{b,level,y},rest}:
      Bool.and(U32.is_eq(id,level),denotes(tail,rest,bindings))
    case Con{C.Value{a,type_id,tag},tail} Con{C.Value{b,typ,t},rest}:
      Bool.and(Bool.and(U32.is_eq(type_id,typ),U32.is_eq(tag,t)),denotes(tail,rest,bindings))
    case Con{C.Construct{a,type_id,tag,ps,args},tail} Con{C.Construct{b,typ,t,qs,refs},rest}:
      Bool.and(Bool.and(Bool.and(U32.is_eq(type_id,typ),U32.is_eq(tag,t)),denotes(args,unfolded(refs,bindings),bindings)),
        denotes(tail,rest,bindings))
    case _ _: False{}

def descendant(candidates: List<&2,C.Binding>, +head: C.Term, +bindings: List<&2,C.Binding>, +smaller: List<&2,U32>) -> Bool:
  match candidates:
    case Nil{}: False{}
    case Con{C.Binding{token,+level,q,+type_id,param,known},tail}:
      Bool.or(Bool.and(contains(smaller,level),denotes([head],[layer(known,C.Reference{token,level,type_id})],bindings)),
        descendant(tail,head,bindings,smaller))

# A rebuilt first argument is the value of the level it denotes, so it
# descends when that level is a strict descendant. References keep descends.
def rebuilt(items: List<&2,C.Term>, +bindings: List<&2,C.Binding>, +smaller: List<&2,U32>) -> Bool:
  match items:
    case Con{C.Reference{token,level,type_id},tail}: False{}
    case Con{head,tail}: descendant(bindings,head,bindings,smaller)
    case Nil{}: False{}

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
    case Scope{+bindings,level,from,live,smaller}:
      S.choose(Result<S.Error,C.Binding>,S.matches(name,"_"),u => C.invalid(C.Binding,"free-name",name),u => find(bindings,name))

def unknown(+token: S.Token, +level: U32, +q: U32, +type_id: U32, +live: Bool) -> Result<S.Error,C.Checked>:
  S.choose(Result<S.Error,C.Checked>,Bool.and(live,U32.is_eq(q,0)),u => C.invalid(C.Checked,"erased-live",token),u =>
    Done{C.Checked{C.Reference{token,level,type_id},type_id,S.choose(List<&2,U32>,Bool.and(live,U32.is_eq(q,1)),u => [level],u => Nil{})}})

def occurrence(known: Maybe<&2,C.Term>, +token: S.Token, +level: U32, +q: U32, +type_id: U32, +live: Bool) -> Result<S.Error,C.Checked>:
  match known:
    case Some{C.Value{origin,source_type,tag}}: Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
    case Some{C.Reference{origin,id,typ}}: unknown(token,level,q,type_id,live)
    case Some{C.Case{origin,id,typ,Nil{}}}: unknown(token,level,q,type_id,live)
    case Some{other}: C.internal(C.Checked,"compound-refinement")
    case None{}:
      unknown(token,level,q,type_id,live)

def reference(binding: C.Binding, token: S.Token, scope: Scope) -> Result<S.Error,C.Checked>:
  match binding scope:
    case C.Binding{name,level,q,type_id,param,known} Scope{bindings,next,from,live,smaller}:
      occurrence(known,token,level,q,type_id,live)

def live_scope(scope: Scope, q: U32) -> Scope:
  match scope:
    case Scope{bindings,next,from,live,smaller}: Scope{bindings,next,from,Bool.and(live,U32.is_ne(q,0)),smaller}

def extend(scope: Scope, token: S.Token, q: U32, type_id: U32) -> Scope:
  match scope:
    case Scope{bindings,+next,from,live,smaller}:
      Scope{Con{C.Binding{token,next,q,type_id,False{},None{}},bindings},U32.add(next,1),Nil{},live,smaller}

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
    case Scope{bindings,next,from,live,smaller}: Scope{refine(bindings,level,tag),next,after(from,level),live,smaller}

# A default region narrows the constructor set, never the runtime value.
# A self-reference marks that distinction without reconstructing a constructor.
def residual(scope: Scope, binding: C.Binding, +empty: Bool) -> Scope:
  match scope binding:
    case Scope{bindings,next,open,live,smaller} C.Binding{+token,+level,q,+type_id,param,known}:
      Scope{replace(bindings,level,S.choose(C.Term,empty,u => C.Case{token,level,type_id,Nil{}},u => C.Reference{token,level,type_id})),
        next,Con{level,after(open,level)},live,smaller}

def uninhabited(types: List<&2,C.Datatype>, +type_id: U32) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{C.Datatype{token,data,ctors},tail}:
      S.choose(Bool,U32.is_eq(type_id,0),u => List.is_empty(&2,C.Constructor,ctors),u => uninhabited(tail,U32.sub(type_id,1)))

# A binder's constructor set is empty for an emptied residual or an empty datatype.
def empty(known: Maybe<&2,C.Term>, types: List<&2,C.Datatype>, +type_id: U32) -> Bool:
  match known:
    case Some{C.Case{token,level,typ,Nil{}}}: True{}
    case _: uninhabited(types,type_id)

# The seed's check-efq: a missing arm is dead code when a live binder in
# context has an empty constructor set. The context is every binder outside
# the pending suffix of the match frontier, which starts at the scrutinee.
# A residual stays pending ahead of later columns, so it witnesses them all.
def witnessed(bindings: List<&2,C.Binding>, +types: List<&2,C.Datatype>, +pending: List<&2,U32>) -> Bool:
  match bindings:
    case Nil{}: False{}
    case Con{C.Binding{token,+level,q,+type_id,param,known},tail}:
      Bool.or(Bool.and(Bool.not(contains(pending,level)),Bool.and(U32.is_ne(q,0),empty(known,types,type_id))),
        witnessed(tail,types,pending))

def dead(scope: Scope, types: List<&2,C.Datatype>, +level: U32) -> Bool:
  match scope:
    case Scope{bindings,next,open,live,smaller}: witnessed(bindings,types,Con{level,after(open,level)})

def parameters(params: List<&2,C.Parameter>, +index: U32, +bindings: List<&2,C.Binding>) -> Scope:
  match params:
    case Nil{}: Scope{bindings,index,List.reverse(&2,U32,levels(bindings)),True{},Nil{}}
    case Con{C.Parameter{token,q,type_id},tail}:
      parameters(tail,U32.add(index,1),Con{C.Binding{token,index,q,type_id,True{},None{}},bindings})

def matchable(binding: C.Binding, +token: S.Token, scope: Scope) -> Result<S.Error,C.Binding>:
  match binding scope:
    case C.Binding{name,level,q,type_id,param,Some{C.Reference{a,b,c}}} _:
      C.unsupported(C.Binding,"default-scrutinee",token)
    case C.Binding{name,level,q,type_id,param,Some{C.Case{a,b,c,Nil{}}}} _:
      C.unsupported(C.Binding,"default-scrutinee",token)
    case C.Binding{+name,+level,+q,+type_id,+param,None{}} Scope{bindings,next,from,live,smaller}:
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
