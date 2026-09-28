import Base
import ./syntax.bend as S
import ./core.bend as C
import ./types.bend as T
import ./generic-catalog.bend as G

def type_id(typ: T.Expr) -> U32:
  match typ:
    case T.Family{index}: index
    case T.Apply{function,argument}: type_id(function)
    case _: 0

def parameter(param: G.Parameter) -> C.Parameter:
  match param:
    case G.Parameter{token,q,typ}: C.Parameter{token,q,type_id(typ)}

def parameters(params: List<&2,G.Parameter>) -> List<&2,C.Parameter>:
  match params:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{parameter(head),parameters(tail)}

def signature(sig: G.Signature) -> C.Signature:
  match sig:
    case G.Signature{token,params,result,body}: C.Signature{token,parameters(params),type_id(result)}

# A zero-quantity suffix selects boxed representation without a live slot.
def append(-A: Data, items: List<&2,A>, marker: A, generic: Bool) -> List<&2,A>:
  match generic:
    case False{}: items
    case True{}: List.append(&2,A,items,[marker])

def fields(token: S.Token, params: List<&2,G.Parameter>, generic: Bool) -> List<&2,C.Parameter>:
  append(C.Parameter,parameters(params),C.Parameter{token,0,0},generic)

def arguments(token: S.Token, args: List<&2,C.Term>, generic: Bool) -> List<&2,C.Term>:
  append(C.Term,args,C.Value{token,0,0},generic)

def bindings(token: S.Token, params: List<&2,C.Binding>, generic: Bool) -> List<&2,C.Binding>:
  append(C.Binding,params,C.Binding{token,0,0,0,False{},None{}},generic)

def construct(+token: S.Token, typ: T.Expr, tag: U32, params: List<&2,G.Parameter>, args: List<&2,C.Term>, +generic: Bool) -> C.Term:
  match params args generic:
    case Nil{} Nil{} False{}: C.Value{token,type_id(typ),tag}
    case +ps +xs +g: C.Construct{token,type_id(typ),tag,fields(token,ps,g),arguments(token,xs,g)}

def constructors(ctors: List<&2,G.Constructor>, +generic: Bool) -> List<&2,C.Constructor>:
  match ctors:
    case Nil{}: Nil{}
    case Con{G.Constructor{+token,params},tail}:
      Con{C.Constructor{token,fields(token,params,generic)},constructors(tail,generic)}

def family(value: G.Family) -> C.Datatype:
  match value:
    case G.Family{token,params,kind,ctors,generic}:
      C.Datatype{token,T.equal(T.normalize(kind),G.data()),constructors(ctors,generic)}

def families(values: List<&2,G.Family>) -> List<&2,C.Datatype>:
  match values:
    case Nil{}: Nil{}
    case Con{head,tail}: Con{family(head),families(tail)}
