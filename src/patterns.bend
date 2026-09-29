import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./catalog.bend as G

type Fields is Data:
  Fields{scope: E.Scope, bindings: List<&2,C.Binding>, arguments: List<&2,C.Term>}

def quantity(+field: U32, +parent: U32, +mark: U32) -> U32:
  S.choose(U32,Bool.or(U32.is_eq(field,0),U32.is_eq(parent,0)),u => 0,u =>
    S.choose(U32,Bool.or(U32.is_eq(field,2),Bool.or(U32.is_eq(parent,2),U32.is_eq(mark,2))),u => 2,u => 1))

def add(scope: E.Scope, +token: S.Token, +q: U32, +type_id: U32, next: E.Scope -> C.Binding -> C.Term -> Result<S.Error,Fields>) -> Result<S.Error,Fields>:
  match scope:
    case E.Scope{+bindings,+level,+open,+live,+smaller}:
      S.choose(Result<S.Error,Fields>,U32.is_ge(level,4096),u => C.exhausted(Fields,token),u =>
        +binding : C.Binding = C.Binding{token,level,q,type_id,True{},None{}}
        next(E.Scope{Con{binding,bindings},U32.add(level,1),open,live,smaller},binding,C.Reference{token,level,type_id}))

def binder(node: S.Node, next: S.Token -> U32 -> Result<S.Error,Fields>) -> Result<S.Error,Fields>:
  match node:
    case S.Variable{token}: next(token,1)
    case S.Promotion{token}: next(token,2)
    case S.Constructor{token,args}: C.unsupported(Fields,"nested-field-pattern",token)
    case S.Call{token,args}: C.invalid(Fields,"pattern-form",token)
    case _: C.internal(Fields,"pattern-field-node")

def prepend(binding: C.Binding, term: C.Term, fields: Fields) -> Fields:
  match fields:
    case Fields{scope,bindings,args}: Fields{scope,Con{binding,bindings},Con{term,args}}

def fields(nodes: List<&2,S.Node>, parameters: List<&2,C.Parameter>, +parent: U32,
  +types: List<&2,C.Datatype>, +scope: E.Scope, +origin: S.Token) -> Result<S.Error,Fields>:
  match nodes parameters:
    case Nil{} Nil{}: Done{Fields{scope,Nil{},Nil{}}}
    case Con{node,+tail} Con{C.Parameter{name,+q,+type_id},+rest}:
      binder(node,+token => +mark =>
        S.bind(Unit,Fields,G.binder(types,token,U32.is_eq(mark,2)),u =>
          add(scope,token,quantity(q,parent,mark),type_id,bound => binding => term =>
            S.bind(Fields,Fields,fields(tail,rest,parent,types,bound,origin),remaining => Done{prepend(binding,term,remaining)}))))
    case _ _: C.invalid(Fields,"pattern-arity",origin)

def value(+token: S.Token, +type_id: U32, +tag: U32, parameters: List<&2,C.Parameter>, args: List<&2,C.Term>) -> C.Term:
  match parameters:
    case Nil{}: C.Value{token,type_id,tag}
    case Con{head,tail}: C.Construct{token,type_id,tag,Con{head,tail},args}

def finish(fields: Fields, token: S.Token, +level: U32, type_id: U32, tag: U32, params: List<&2,C.Parameter>) -> Fields:
  match fields:
    case Fields{scope,Nil{},args}: Fields{scope,Nil{},args}
    case Fields{E.Scope{bindings,next,open,live,smaller},Con{+head,+tail},+args}:
      +introduced : List<&2,C.Binding> = Con{head,tail}
      Fields{E.Scope{E.replace(bindings,level,value(token,type_id,tag,params,args)),next,
        List.append(&2,U32,E.levels(introduced),open),live,E.descendants(level,E.levels(introduced),smaller)},introduced,args}

def open_fields(binding: C.Binding, +scope: E.Scope, +tag: U32, +nodes: List<&2,S.Node>, +params: List<&2,C.Parameter>, +types: List<&2,C.Datatype>) -> Result<S.Error,Fields>:
  match binding:
    case C.Binding{+token,+level,q,+type_id,param,known}:
      S.bind(Fields,Fields,fields(nodes,params,q,types,E.branch(scope,level,tag),token),result => Done{finish(result,token,level,type_id,tag,params)})

# A `+` mark may raise a frontier binder past its type's kind. As in the seed,
# the kind is judged only where the frontier binds the binder: on leaving it
# undestructured, ahead of a matched level (advance) or at a body that is not
# a match (close). A binder destructured first is never bound; its fields are.
def kind(binding: C.Binding, types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match binding:
    case C.Binding{token,level,q,type_id,param,known}:
      S.bind(C.Datatype,Unit,G.type_at(types,type_id),definition => G.quantity(token,q,definition))

def bound(levels: List<&2,U32>, +bindings: List<&2,C.Binding>, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match levels:
    case Nil{}: Done{Unit{}}
    case Con{level,tail}:
      S.bind(C.Binding,Unit,E.find_level(bindings,level),binding =>
        S.bind(Unit,Unit,kind(binding,types),u => bound(tail,bindings,types)))

def advance(scope: E.Scope, +level: U32, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match scope:
    case E.Scope{+bindings,next,open,live,smaller}: bound(E.ahead(open,level),bindings,types)

def close(scope: E.Scope, +types: List<&2,C.Datatype>) -> Result<S.Error,E.Scope>:
  match scope:
    case E.Scope{+bindings,next,open,live,smaller}:
      S.bind(Unit,E.Scope,bound(open,bindings,types),u => Done{E.Scope{bindings,next,Nil{},live,smaller}})

def branch(+scope: E.Scope, +level: U32, reference: G.ConstructorRef, node: S.Node, +types: List<&2,C.Datatype>) -> Result<S.Error,Fields>:
  match scope reference node:
    case E.Scope{bindings,next,open,live,smaller} G.ConstructorRef{+type_id,+tag} S.Constructor{token,+args}:
      S.bind(Unit,Fields,advance(scope,level,types),u =>
        S.bind(List<&2,C.Parameter>,Fields,G.field_signature(G.ConstructorRef{type_id,tag},types),+params =>
          S.bind(C.Binding,Fields,E.find_level(bindings,level),binding => open_fields(binding,scope,tag,args,params,types))))
    case _ _ _: C.internal(Fields,"branch-pattern")
