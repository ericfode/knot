import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G

def kind_name(kind: U32) -> String:
  match kind:
    case 0: "U32"
    case 1: "Nat"
    case 2: "Char"
    case _: "String"

def installed(token: S.Token) -> Bool:
  match token:
    case S.Token{name,S.At{start,end,line,column}}: U32.is_eq(line,0)

def kind(definition: C.Datatype) -> Maybe<&2,U32>:
  match definition:
    case C.Datatype{+token,data,ctors}:
      S.choose(Maybe<&2,U32>,installed(token),u =>
      S.choose(Maybe<&2,U32>,S.matches(token,"U32"),u => Some{0},u =>
      S.choose(Maybe<&2,U32>,S.matches(token,"Nat"),u => Some{1},u =>
      S.choose(Maybe<&2,U32>,S.matches(token,"Char"),u => Some{2},u =>
      S.choose(Maybe<&2,U32>,S.matches(token,"String"),u => Some{3},u => None{})))),u => None{})

def is_kind(types: List<&2,C.Datatype>, +index: U32, +wanted: U32) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{C.Datatype{+token,data,ctors},+tail}:
      S.choose(Bool,U32.is_eq(index,0),u => Bool.and(installed(token),S.matches(token,kind_name(wanted))),u => is_kind(tail,U32.sub(index,1),wanted))

def find(types: List<&2,C.Datatype>, +name: String, +index: U32) -> Result<S.Error,U32>:
  match types:
    case Nil{}: Fail{S.Internal{"eval","primitive-type"}}
    case Con{C.Datatype{+token,data,ctors},+tail}:
      S.choose(Result<S.Error,U32>,Bool.and(installed(token),S.matches(token,name)),u => Done{index},u => find(tail,name,U32.add(index,1)))

def primitive_type(types: List<&2,C.Datatype>, name: String) -> Result<S.Error,U32>:
  find(types,name,0)

def present(types: List<&2,C.Datatype>, +name: String) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{C.Datatype{+token,data,ctors},+tail}:
      Bool.or(Bool.and(installed(token),S.matches(token,name)),present(tail,name))

# Base spells U32{data: Word(32n)}, but an installed U32 is unboxed bits.
def constructor(+types: List<&2,C.Datatype>, +token: S.Token) -> Result<S.Error,G.ConstructorRef>:
  S.choose(Result<S.Error,G.ConstructorRef>,Bool.and(S.matches(token,"U32"),present(types,"U32")),u =>
    C.unsupported(G.ConstructorRef,"u32-constructor",token),u => G.find_constructor(types,token,0))
