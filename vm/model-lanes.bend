import Base
import ./model/word.bend as W

# The seed's two lanes on the shapes its native lane misreads (MODEL.md): a U32
# comparison against a nullary call (`limit`, `W.none`) or a constant-argument
# one (`W.is_none(0)`), as either operand of a disjunction or an exclusive or.
# Each row prints one word x, then W's seven columns, then the same seven
# through Base's Bool.or and Bool.xor. The vm-model gate builds this natively
# and requires W's columns to be the comparisons' values on both lanes.

def limit() -> U32:
  1048576

def bits(xs: List<Bool>) -> String:
  match xs:
    case Nil{}: ""
    case Con{x,rest}: String.append(U32.show(Bool.to_u32(x)),bits(rest))

def row(+x: U32) -> String:
  String.concat([U32.show(x),"\t",
    bits([W.or(U32.is_gt(x,limit()),False{}),W.or(False{},U32.is_gt(x,limit())),
          W.xor(U32.is_gt(x,limit()),True{}),W.xor(True{},U32.is_gt(x,limit())),
          W.or(W.is_none(x),False{}),W.or(W.is_none(0),False{}),W.or(U32.is_eq(x,W.none()),U32.is_eq(x,3))]),"\t",
    bits([Bool.or(U32.is_gt(x,limit()),False{}),Bool.or(False{},U32.is_gt(x,limit())),
          Bool.xor(U32.is_gt(x,limit()),True{}),Bool.xor(True{},U32.is_gt(x,limit())),
          Bool.or(W.is_none(x),False{}),Bool.or(W.is_none(0),False{}),Bool.or(U32.is_eq(x,W.none()),U32.is_eq(x,3))])])

# Literal words first, then each argument read at run time.
def rows(args: List<String>) -> List<String>:
  match args:
    case Nil{}: Nil{}
    case Con{a,rest}: Con{row(Maybe.default(&2,U32,U32.read(a),0)),rows(rest)}

def shown(lines: List<String>) -> IO(Unit):
  match lines:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{line,rest}: IO.bind(Unit,Unit,IO.print(line),u => shown(rest))

def lanes(args: List<String>) -> IO(Unit):
  shown(List.concat(&1,String,[[row(3),row(2000000),row(4294967295)],rows(args)]))

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),lanes)
