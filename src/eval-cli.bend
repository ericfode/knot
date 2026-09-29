import Base
import ./syntax.bend as S
import ./core.bend as C
import ./driver.bend as D
import ./eval.bend as E

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
    case Done{+request}: D.load(path,D.Limits{65536n,512n,512n},book => evaluate(book,name,request))

def module_configured(root: String, path: String, +name: String, result: Result<S.Error,Request>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+request}: D.bundle(path,root,D.Limits{65536n,512n,4096n},book => evaluate(book,name,request))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{name,Con{budget,values}}}:
      configured(path,name,S.bind(Nat,Request,D.natural(U32.read(budget),1048576),fuel =>
        S.bind(List<&2,U32>,Request,D.ordinals(values),xs => Done{Request{fuel,xs}})))
    case _: D.fail(S.Host{"arguments","expected source function transition-budget [live-ordinals...]"})

def module_arguments(root: String, args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{name,Con{budget,values}}}:
      module_configured(root,path,name,S.bind(Nat,Request,D.natural(U32.read(budget),1048576),fuel =>
        S.bind(List<&2,U32>,Request,D.ordinals(values),xs => Done{Request{fuel,xs}})))
    case _: D.fail(S.Host{"arguments","expected --bundle root source function transition-budget [live-ordinals...]"})

def select(flag: String, root: String, rest: List<String>, module: Bool) -> IO(Unit):
  match module:
    case True{}: module_arguments(root,rest)
    case False{}: arguments(Con{flag,Con{root,rest}})

def dispatch(args: List<String>) -> IO(Unit):
  match args:
    case Con{+flag,Con{root,rest}}: select(flag,root,rest,String.eq(flag,"--bundle"))
    case _: arguments(args)

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),dispatch)
