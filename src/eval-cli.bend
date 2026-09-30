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

def abstract_parameters(params: List<&2,C.Parameter>) -> Bool:
  match params:
    case Nil{}: False{}
    case Con{C.Parameter{token,q,typ},tail}:
      Bool.or(Bool.and(Bool.not(U32.is_eq(q,0)),U32.is_eq(typ,4294967295)),abstract_parameters(tail))

def entry(+book: C.Book, +name: String, request: Request,
  found: Result<S.Error,C.Function>) -> IO(Unit):
  match request found:
    case _ Fail{e}: D.fail(e)
    case Request{+fuel,+args} Done{C.Function{C.Signature{token,params,result},body}}:
      S.choose(IO(Unit),Bool.or(U32.is_eq(result,4294967295),abstract_parameters(params)),u =>
        D.fail(S.Host{"invoke","abstract-signature"}),u => evaluated(book,E.invoke(book,name,args,fuel)))

def evaluate(+book: C.Book, +name: String, request: Request) -> IO(Unit):
  match book:
    case C.Book{types,functions}: entry(book,name,request,E.function_named(functions,name))

def configured(path: String, +name: String, result: Result<S.Error,Request>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+request}: D.load(path,D.Limits{65536n,512n,512n},book => evaluate(book,name,request))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{name,Con{budget,values}}}:
      configured(path,name,S.bind(Nat,Request,D.natural(U32.read(budget),1048576),fuel =>
        S.bind(List<&2,U32>,Request,D.ordinals(values),xs => Done{Request{fuel,xs}})))
    case _: D.fail(S.Host{"arguments","expected source function transition-budget [live-ordinals...]"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
