import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./literal-base.bend as B
import ./primitive-op.bend as R
import ./literal-types.bend as T
import ./primitive.bend as O

# A literal takes the installed primitive of its kind. Without it the seed
# spells the literal by bare constructor names (the matrix's expansion), so a
# target that declares the spelled constructor may accept it, and Knot does not
# interpret that spelling. A U32 or Char word spells Base's Word, which Knot does
# not model: any target may spell it.
def declares(found: Result<S.Error,G.ConstructorRef>, +target: U32) -> Bool:
  match found:
    case Done{G.ConstructorRef{type_id,tag}}: U32.is_eq(type_id,target)
    case Fail{error}: False{}

def spells(+types: List<&2,C.Datatype>, target: Maybe<&2,U32>, spelling: S.Node) -> Bool:
  match target spelling:
    case None{} _: False{}
    case Some{+id} S.Constructor{+name,args}: declares(G.find_constructor(types,name,0),id)
    case Some{id} _: True{}

def primitive_type(+types: List<&2,C.Datatype>, +kind: U32, +token: S.Token, target: Maybe<&2,U32>, spelling: S.Node) -> Result<S.Error,U32>:
  S.choose(Result<S.Error,U32>,T.present(types,B.kind_name(kind)),u => T.primitive_type(types,B.kind_name(kind)),u =>
    S.choose(Result<S.Error,U32>,spells(types,target,spelling),u => C.unsupported(U32,"literal-base-type",token),u => C.invalid(U32,"unknown-type",token)))

def literal(+token: S.Token, +kind: U32, +number: U32, +text: List<&2,U32>, +types: List<&2,C.Datatype>, target: Maybe<&2,U32>, spelling: S.Node) -> Result<S.Error,C.Checked>:
  S.bind(U32,C.Checked,primitive_type(types,kind,token,target,spelling),+id =>
    Done{C.Checked{S.choose(C.Term,Bool.or(U32.is_eq(kind,0),U32.is_eq(kind,2)),u => C.Value{token,id,number},u => C.Literal{token,id,kind,number,text}),id,Nil{}}})

def arguments(+op: R.Op, types: List<&2,C.Datatype>) -> Result<S.Error,List<&2,C.Parameter>>:
  G.parameters(B.parameters(O.inputs(op),O.quantities(op),0),types,0)

def result(value: C.Checked, token: S.Token, +type_id: U32, op: R.Op) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{C.Sequence{args},ignored,uses}: Done{C.Checked{C.Intrinsic{token,type_id,op,args},type_id,uses}}
    case _: C.internal(C.Checked,"intrinsic-arguments")

def constructor(value: C.Checked, +types: List<&2,C.Datatype>) -> Result<S.Error,C.Checked>:
  match value:
    case C.Checked{C.Construct{+token,typ,tag,params,+args},+type_id,uses}:
      Done{C.Checked{S.choose(C.Term,T.is_kind(types,type_id,2),u => C.Intrinsic{token,type_id,R.FromCode{},args},u => C.Construct{token,typ,tag,params,args}),type_id,uses}}
    case _: Done{value}

def intrinsic_type(reference: G.TypeRef, next: U32 -> Result<S.Error,C.Checked>) -> Result<S.Error,C.Checked>:
  match reference:
    case G.TypeRef{id,definition}: next(id)
