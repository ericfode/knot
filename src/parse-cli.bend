import Base
import ./syntax.bend as S
import ./lex.bend as L
import ./parse.bend as P
import ./diagnostic.bend as D

def show_tree(result: Result<S.Error,String>) -> IO(Unit):
  match result:
    case Fail{+e}: IO.die(Unit,D.status(e),D.error(e))
    case Done{text}: IO.print(String.append("Parsed\t",text))

def show_parse(result: Result<S.Error,P.Parsed>) -> IO(Unit):
  match result:
    case Fail{+e}: IO.die(Unit,D.status(e),D.error(e))
    case Done{P.Parsed{value,rest}}: show_tree(D.tree(4096n,value))

def source(characters: Nat, +depth: Nat, text: String) -> IO(Unit):
  show_parse(S.bind(List<&2,S.Token>,P.Parsed,L.tokenize(characters,text),tokens => P.parse(depth,tokens)))

def read_result(characters: Nat, depth: Nat, result: Result<&1,&1,U32 & String,String>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\tread\t",U32.show(code),"\t",message]))
    case Done{text}: source(characters,depth,text)

def read_pair(characters: Nat, depth: Nat, pair: File & Result<&1,&1,U32 & String,String>) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    read_result(characters,depth,result)

def opened(characters: Nat, depth: Nat, result: Result<&1,&1,U32 & String,File>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,65537),read_pair(characters,depth))

def open_source(path: String, characters: Nat, depth: Nat) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),opened(characters,depth))

def configure(+path: String, chars: Maybe<&2,U32>, depth: Maybe<&2,U32>) -> IO(Unit):
  match chars depth:
    case Some{+c} Some{+d}:
      S.choose(IO(Unit),Bool.and(U32.is_le(c,65536),U32.is_le(d,4096)),u =>
        open_source(path,U32.to_nat(c),U32.to_nat(d)),u =>
        IO.die(Unit,5,"HostFailure\targuments\tbudget-out-of-range"))
    case _ _: IO.die(Unit,5,"HostFailure\targuments\tinvalid-budget")

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}:
      open_source(path,65536n,512n)
    case Con{path,Con{chars,Con{depth,Nil{}}}}:
      configure(path,U32.read(chars),U32.read(depth))
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected path [character-budget parser-depth]")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
