import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E

type Local is Data:
  Local{level: U32, index: U32, quantity: U32, type_id: U32}
type Layout is Data:
  Layout{type_id: U32, tag: U32, reusable: Bool, edges: List<&2,Bool>}
type Use is Data:
  Term{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}
  Arms{terms: List<&2,C.Term>}

def fielded(constructors: List<&2,C.Constructor>) -> Bool:
  match constructors:
    case Nil{}: False{}
    case Con{C.Constructor{token,Nil{}},tail}: fielded(tail)
    case Con{C.Constructor{token,Con{head,tail}},rest}: True{}

def boxed(types: List<&2,C.Datatype>, +index: U32) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{C.Datatype{token,reusable,+constructors},+tail}:
      S.choose(Bool,U32.is_eq(index,0),u => fielded(constructors),u => boxed(tail,U32.sub(index,1)))

def edges(parameters: List<&2,C.Parameter>, +types: List<&2,C.Datatype>) -> List<&2,Bool>:
  match parameters:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,q,+type_id},+tail}:
      S.choose(List<&2,Bool>,U32.is_eq(q,0),u => edges(tail,types),u => Con{boxed(types,type_id),edges(tail,types)})

def constructors(items: List<&2,C.Constructor>, +types: List<&2,C.Datatype>, +id: U32, +tag: U32, +reusable: Bool) -> List<&2,Layout>:
  match items:
    case Nil{}: Nil{}
    case Con{C.Constructor{token,fields},tail}:
      Con{Layout{id,tag,reusable,edges(fields,types)},constructors(tail,types,id,U32.add(tag,1),reusable)}

def layouts(items: List<&2,C.Datatype>, +types: List<&2,C.Datatype>, +id: U32) -> List<&2,Layout>:
  match items:
    case Nil{}: Nil{}
    case Con{C.Datatype{token,+reusable,+ctors},+tail}:
      S.choose(List<&2,Layout>,fielded(ctors),u =>
        List.append(&2,Layout,constructors(ctors,types,id,0,reusable),layouts(tail,types,U32.add(id,1))),u => layouts(tail,types,U32.add(id,1)))

def layout(items: List<&2,Layout>, +type_id: U32, +tag: U32, +index: U32) -> Result<S.Error,U32>:
  match items:
    case Nil{}: C.internal(U32,"owned-layout")
    case Con{Layout{id,t,reusable,edges},+tail}:
      S.choose(Result<S.Error,U32>,Bool.and(U32.is_eq(id,type_id),U32.is_eq(t,tag)),u => Done{index},u => layout(tail,type_id,tag,U32.add(index,1)))

def signature(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,List<&2,C.Parameter>>:
  match functions:
    case Nil{}: C.internal(List<&2,C.Parameter>,"owned-function")
    case Con{C.Function{C.Signature{token,+params,result},body},+tail}:
      S.choose(Result<S.Error,List<&2,C.Parameter>>,U32.is_eq(index,0),u => Done{params},u => signature(tail,U32.sub(index,1)))

# This is runtime liveness, including reusable bindings. Erased terms add no
# use; arm-local identities cannot escape into the incoming environment.
def needs(fuel: Nat, use: Use, +functions: List<&2,C.Function>) -> Result<S.Error,List<&2,U32>>:
  match fuel use:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+n Term{C.Value{token,type_id,tag}}: Done{Nil{}}
    case 1n+n Term{C.Reference{token,level,type_id}}: Done{[level]}
    case 1n+n Term{C.Construct{token,type_id,tag,params,args}}: needs(n,Arguments{args,params},functions)
    case 1n+ +n Term{C.Application{token,index,type_id,+args}}:
      S.bind(List<&2,C.Parameter>,List<&2,U32>,signature(functions,index),params => needs(n,Arguments{args,params},functions))
    case 1n+ +n Term{C.Let{token,+level,+q,type_id,+value,body}}:
      S.bind(List<&2,U32>,List<&2,U32>,needs(n,Term{body},functions),+rest =>
        S.choose(Result<S.Error,List<&2,U32>>,U32.is_eq(q,0),u => Done{E.remove(rest,level)},u =>
          S.bind(List<&2,U32>,List<&2,U32>,needs(n,Term{value},functions),used => Done{E.alternatives(used,E.remove(rest,level))})))
    case 1n+n Term{C.Case{token,+level,type_id,arms}}:
      S.bind(List<&2,U32>,List<&2,U32>,needs(n,Arms{arms},functions),used => Done{E.alternatives([level],used)})
    case 1n+n Term{term}: C.internal(List<&2,U32>,"owned-use-node")
    case 1n+n Arguments{Nil{},Nil{}}: Done{Nil{}}
    case 1n+ +n Arguments{Con{+head,tail},Con{C.Parameter{token,+q,type_id},params}}:
      S.bind(List<&2,U32>,List<&2,U32>,needs(n,Arguments{tail,params},functions),+rest =>
        S.choose(Result<S.Error,List<&2,U32>>,U32.is_eq(q,0),u => Done{rest},u =>
          S.bind(List<&2,U32>,List<&2,U32>,needs(n,Term{head},functions),used => Done{E.alternatives(used,rest)})))
    case 1n+n Arguments{terms,params}: C.internal(List<&2,U32>,"owned-use-arity")
    case 1n+n Arms{Nil{}}: Done{Nil{}}
    case 1n+ +n Arms{Con{C.Branch{tag,+fields,body},+tail}}:
      S.bind(List<&2,U32>,List<&2,U32>,needs(n,Term{body},functions),+used =>
        S.bind(List<&2,U32>,List<&2,U32>,needs(n,Arms{tail},functions),rest => Done{E.alternatives(E.remove_fields(fields,used),rest)}))
    case 1n+n Arms{terms}: C.internal(List<&2,U32>,"owned-use-arm")

def keep(locals: List<&2,Local>, +used: List<&2,U32>) -> List<&2,Local>:
  match locals:
    case Nil{}: Nil{}
    case Con{+head,+tail}:
      match head:
        case Local{level,index,q,type_id}:
          S.choose(List<&2,Local>,E.contains(used,level),u => Con{head,keep(tail,used)},u => keep(tail,used))

def lookup(locals: List<&2,Local>, +level: U32) -> Result<S.Error,Local>:
  match locals:
    case Nil{}: C.internal(Local,"owned-local")
    case Con{+head,+tail}:
      match head:
        case Local{id,index,q,type_id}:
          S.choose(Result<S.Error,Local>,U32.is_eq(id,level),u => Done{head},u => lookup(tail,level))

def parameters(params: List<&2,C.Parameter>, +level: U32, +index: U32) -> List<&2,Local>:
  match params:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,+q,+type_id},+tail}:
      S.choose(List<&2,Local>,U32.is_eq(q,0),u => parameters(tail,U32.add(level,1),index),u =>
        Con{Local{level,index,q,type_id},parameters(tail,U32.add(level,1),U32.add(index,1))})

def share(quantity: U32, future: List<&2,U32>, level: U32) -> Bool:
  Bool.and(U32.is_eq(quantity,2),E.contains(future,level))
