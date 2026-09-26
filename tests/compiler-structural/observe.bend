import Base
import ../../src/syntax.bend as S
import ../../src/lex.bend as L
import ../../src/parse.bend as P
import ../../src/catalog.bend as G
import ../../src/core.bend as C
import ../../src/diagnostic.bend as D

# This observer renders the actual catalog. It neither checks function bodies
# nor evaluates source programs; Catalogued is not executable acceptance.
def fields(items: List<&2,C.Parameter>) -> String:
  match items:
    case Nil{}: ""
    case Con{C.Parameter{+token,q,type_id},tail}:
      String.concat([S.text(token),"@",D.location(S.at(token)),"=",U32.show(q),":",U32.show(type_id),";",fields(tail)])

def constructors(items: List<&2,C.Constructor>, +index: U32) -> String:
  match items:
    case Nil{}: ""
    case Con{C.Constructor{token,params},tail}:
      String.concat([U32.show(index)," ",S.text(token),"[",fields(params),"];",constructors(tail,U32.add(index,1))])

def types(items: List<&2,C.Datatype>, +index: U32) -> String:
  match items:
    case Nil{}: ""
    case Con{C.Datatype{token,data,ctors},tail}:
      String.concat([U32.show(index)," ",S.text(token),Bool.pick(String,data," Data{"," Type{"),constructors(ctors,0),"}\n",types(tail,U32.add(index,1))])

def catalog(result: Result<S.Error,C.Catalog>) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,D.status(error),D.error(error))
    case Done{C.Catalog{items,signatures}}: IO.print(String.append("Catalogued\n",types(items,0)))

def parsed(result: Result<S.Error,P.Parsed>) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,D.status(error),D.error(error))
    case Done{P.Parsed{value,rest}}: catalog(G.catalog(value))

def read_result(result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,"HostFailure\tread")
    case Done{text}:
      parsed(S.bind(List<&2,S.Token>,P.Parsed,L.tokenize(65536n,text),tokens => P.parse(4096n,tokens)))

def read_pair(pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(result)

def opened(result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,"HostFailure\topen")
    case Done{file}: IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,65537),read_pair)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}:
      IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),opened)
    case _: IO.die(Unit,5,"HostFailure\targuments")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
