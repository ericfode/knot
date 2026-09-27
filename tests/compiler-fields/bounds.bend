import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/scope.bend as E
import ../../src/patterns.bend as P
import ../../src/eval.bend as V
import ../../src/diagnostic.bend as D

def show(result: Result<S.Error,P.Fields>) -> String:
  match result:
    case Fail{e}: D.error(e)
    case Done{P.Fields{E.Scope{bindings,next,open,live},fields,args}}:
      String.append("Next ",U32.show(next))

def add(level: U32) -> Result<S.Error,P.Fields>:
  P.add(E.Scope{Nil{},level,Nil{},True{}},S.Token{"v",S.At{0,0,1,0}},1,0,
    scope => binding => term => Done{P.Fields{scope,[binding],[term]}})

def text(result: Result<S.Error,String>) -> String:
  match result:
    case Fail{e}: D.error(e)
    case Done{value}: value

def main() -> IO(Unit):
  +types : List<&2,C.Datatype> = [C.Datatype{S.Token{"Flag",S.At{0,0,1,0}},True{},[C.Constructor{S.Token{"Off",S.At{0,0,1,0}},Nil{}}]}]
  do IO<Unit>:
    IO.print(show(add(4095)))
    IO.print(show(add(4096)))
    IO.print(text(V.display(0n,V.One{V.Value{0,0}},types)))
    IO.print(text(V.display(2n,V.One{V.Value{0,0}},types)))
    IO.print(text(V.render(1n,[V.Text{"x"}],types,0n,Nil{})))
    IO.print(text(V.render(1n,[V.Text{"x"}],types,1n,Nil{})))
