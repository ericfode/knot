import Base
import ./syntax.bend as S
import ./primitive-op.bend as R
import ./primitive.bend as O

# Only the hash-verified Base loader installs these nodes. The signatures retain
# the seed's quantities; the closed intrinsic set has no surface spelling.
def token(text: String) -> S.Token:
  S.Token{text,S.At{0,0,0,0}}

def parameter(name: String, q: U32, typ: String) -> S.Node:
  S.Parameter{token(name),q,token(typ)}

def parameters(types: List<&2,String>, quantities: List<&2,U32>, +index: U32) -> List<&2,S.Node>:
  match types quantities:
    case Con{typ,tail} Con{q,rest}:
      Con{parameter(String.append("p",U32.show(index)),q,typ),parameters(tail,rest,U32.add(index,1))}
    case _ _: Nil{}

def variables(types: List<&2,String>, +index: U32) -> List<&2,S.Node>:
  match types:
    case Nil{}: Nil{}
    case Con{typ,tail}: Con{S.Variable{token(String.append("p",U32.show(index)))},variables(tail,U32.add(index,1))}

def intrinsic(op: Maybe<&2,R.Op>) -> Maybe<&2,S.Node>:
  match op:
    case None{}: None{}
    case Some{+value}:
      Some{S.Function{token(O.name(value)),parameters(O.inputs(value),O.quantities(value),0),token(O.output(value)),
        S.Intrinsic{token(O.name(value)),value,variables(O.inputs(value),0)}}}

def declaration(+name: String) -> Maybe<&2,S.Node>:
  S.choose(Maybe<&2,S.Node>,String.eq(name,"U32"),u =>
    Some{S.Datatype{token(name),True{},[S.Constructor{token("#U32"),Nil{}}]}},u =>
  S.choose(Maybe<&2,S.Node>,String.eq(name,"Nat"),u =>
    Some{S.Datatype{token(name),True{},[S.Constructor{token("Zero"),Nil{}},S.Constructor{token("Succ"),[parameter("pred",1,"Nat")]}]}},u =>
  S.choose(Maybe<&2,S.Node>,String.eq(name,"Char"),u =>
    Some{S.Datatype{token(name),True{},[S.Constructor{token("Chr"),[parameter("code",1,"U32")]}]}},u =>
  S.choose(Maybe<&2,S.Node>,String.eq(name,"String"),u =>
    Some{S.Datatype{token(name),True{},[S.Constructor{token("SNil"),Nil{}},S.Constructor{token("SCon"),[parameter("head",1,"Char"),parameter("tail",1,"String")]}]}},u =>
    intrinsic(O.lookup(name))))))

def kind_name(kind: U32) -> String:
  match kind:
    case 0: "U32"
    case 1: "Nat"
    case 2: "Char"
    case _: "String"

def installed(token: S.Token) -> Bool:
  match token:
    case S.Token{name,S.At{start,end,line,column}}: U32.is_eq(line,0)
