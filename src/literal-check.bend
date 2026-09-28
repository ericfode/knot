import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./literal-base.bend as B
import ./primitive-op.bend as R
import ./literal-types.bend as T
import ./primitive.bend as O

# A literal spells an installed primitive. A book's own datatype of that name
# is outside this profile: the seed accepts it when its constructors fit.
def type_id(reference: G.TypeRef) -> Result<S.Error,U32>:
  match reference:
    case G.TypeRef{index,C.Datatype{+token,data,ctors}}:
      S.choose(Result<S.Error,U32>,B.installed(token),u => Done{index},u => C.unsupported(U32,"literal-base-type",token))

def primitive_type(types: List<&2,C.Datatype>, name: String) -> Result<S.Error,U32>:
  S.bind(G.TypeRef,U32,G.find_type(types,B.token(name),0),type_id)


def literal(+token: S.Token, +kind: U32, +number: U32, +text: List<&2,U32>, types: List<&2,C.Datatype>) -> Result<S.Error,C.Checked>:
  S.bind(U32,C.Checked,primitive_type(types,B.kind_name(kind)),+id =>
    Done{C.Checked{S.choose(C.Term,Bool.or(U32.is_eq(kind,0),U32.is_eq(kind,2)),u => C.Value{token,id,number},u => C.Literal{token,id,kind,number,text}),id,Nil{}}})

def arguments(+op: R.Op, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:
  G.parameters(B.parameters(O.inputs(op),O.quantities(op),0),types,0)

def result(value: C.Checked, token: S.Token, +type_id: U32, op: R.Op) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{C.Sequence{args},ignored,uses}: Done{C.Checked{C.Intrinsic{token,type_id,op,args},type_id,uses}}
    case _: C.internal(C.Checked,"intrinsic-arguments")

def constructor(term: C.Term, +types: List<&2,C.Datatype>, +type_id: U32) -> C.Term:
  match term:
    case C.Construct{+token,typ,tag,params,+args}:
      S.choose(C.Term,T.is_kind(types,type_id,2),u => C.Intrinsic{token,type_id,R.FromCode{},args},u => C.Construct{token,typ,tag,params,args})
    case _: term
