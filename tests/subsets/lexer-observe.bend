import Base
import ../../src/syntax.bend as S
import ../../src/lex.bend as L
import ../../src/diagnostic.bend as D

def tokens(xs: List<&2,S.Token>) -> String:
  match xs:
    case Nil{}: ""
    case Con{+head,tail}:
      String.concat([Bool.pick(String,S.matches(head,"\n"),"<nl>",S.text(head)),"@",D.location(S.at(head)),";",tokens(tail)])

def show(result: Result<S.Error,List<&2,S.Token>>) -> String:
  match result:
    case Fail{e}: D.error(e)
    case Done{xs}: tokens(xs)

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(show(L.tokenize(20n,"# x\n a ")))
    IO.print(show(L.tokenize(20n,"alpha.beta(foo)")))
    IO.print(show(L.tokenize(1n,"ab")))
    IO.print(show(L.tokenize(0n,"")))
