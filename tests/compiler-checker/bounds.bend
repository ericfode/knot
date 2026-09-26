import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/catalog.bend as G
import ../../src/diagnostic.bend as D

def token(index: U32) -> S.Token:
  S.Token{String.append("N",U32.show(index)),S.At{0,0,1,0}}

def ctors(n: Nat, +index: U32) -> List<&2,S.Node>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{S.Constructor{token(index),Nil{}},ctors(m,U32.add(index,1))}

def types(n: Nat, +index: U32) -> List<&2,S.Node>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{S.Datatype{token(index),False{},[S.Constructor{token(index),Nil{}}]},types(m,U32.add(index,1))}

def params(n: Nat, +index: U32) -> List<&2,S.Node>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{S.Parameter{token(index),1,token(0)},params(m,U32.add(index,1))}

def funcs(n: Nat, +index: U32) -> List<&2,S.Node>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{S.Function{token(index),Nil{},token(0),S.Constructor{token(0),Nil{}}},funcs(m,U32.add(index,1))}

def show(-A: Data, result: Result<S.Error,List<&2,A>>) -> String:
  match result:
    case Done{items}: String.append("Done ",Nat.show(List.length(&2,A,items)))
    case Fail{e}: D.error(e)

def main() -> IO(Unit):
  +ts : List<&2,C.Datatype> = [C.Datatype{token(0),False{},[C.Constructor{token(0),Nil{}}]}]
  do IO<Unit>:
    IO.print(show(C.Constructor,G.constructors(ctors(256n,0),Nil{},0)))
    IO.print(show(C.Constructor,G.constructors(ctors(257n,0),Nil{},0)))
    IO.print(show(C.Datatype,G.collect_types(types(256n,0),0)))
    IO.print(show(C.Datatype,G.collect_types(types(257n,0),0)))
    IO.print(show(C.Parameter,G.parameters(params(256n,0),ts,0)))
    IO.print(show(C.Parameter,G.parameters(params(257n,0),ts,0)))
    IO.print(show(C.Signature,G.collect_signatures(funcs(256n,0),ts,0)))
    IO.print(show(C.Signature,G.collect_signatures(funcs(257n,0),ts,0)))
