import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/eval.bend as E
import ../../src/opt.bend as O

type Request is Data:
  Request{fuel: Nat, arguments: List<&2,U32>}

def print(result: Result<S.Error,String>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{text}: IO.print(text)

def evaluated(+book: C.Book, result: Result<S.Error,E.Value>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{value}: print(E.describe(value,book))

def evaluate(+book: C.Book, name: String, request: Request) -> IO(Unit):
  match request:
    case Request{fuel,args}: evaluated(book,E.invoke(book,name,args,fuel))

def configured(path: String, +name: String, result: Result<S.Error,Request>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+request}: D.load(path,D.Limits{65536n,512n,512n},book => D.checked(O.pipeline(4096n,book),optimized => evaluate(optimized,name,request)))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{name,Con{budget,values}}}:
      configured(path,name,S.bind(Nat,Request,D.natural(U32.read(budget),1048576),fuel =>
        S.bind(List<&2,U32>,Request,D.ordinals(values),xs => Done{Request{fuel,xs}})))
    case _: D.fail(S.Host{"arguments","expected source function transition-budget [live-ordinals...]"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
