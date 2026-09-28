import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/compile-cli.bend as CLI
import ../../src/c.bend as E

# C text can exceed a megabyte. Count with a tail loop; Base.List.length builds
# a non-tail continuation per byte in the Bun seed lane.
def count(bytes: List<&2,U32>, size: U32) -> U32:
  match bytes:
    case Nil{}: size
    case Con{head,tail}: count(tail,U32.add(size,1))

def opened(result: Result<&1,&1,U32 & String,File>, bytes: List<&2,U32>, +size: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\toutput-open\t",U32.show(code),"\t",message]))
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),pair => CLI.write_pair(pair,size))

def emitted(path: String, result: Result<S.Error,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+bytes}:
      +size = count(bytes,0)
      IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),result => opened(result,bytes,size))

def compile(book: C.Book, path: String, options: CLI.Options) -> IO(Unit):
  match options:
    case CLI.Options{input,depth,bytes}:
      emitted(path,E.emit(book,depth,bytes))

def configured(+source: String, +path: String, result: Result<S.Error,CLI.Options>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+options}:
      match options:
        case CLI.Options{input,depth,bytes}:
          S.choose(IO(Unit),String.eq(source,path),u => D.fail(S.Host{"arguments","source-is-output"}),u =>
            D.load(source,input,book => compile(book,path,options)))

def capacity(options: CLI.Options, bytes: U32) -> CLI.Options:
  match options:
    case CLI.Options{input,depth,old}: CLI.Options{input,depth,bytes}

def budgets(chars: String, parser: String, checker: String, depth: String, +bytes: String) -> Result<S.Error,CLI.Options>:
  S.bind(CLI.Options,CLI.Options,CLI.budgets(chars,parser,checker,depth,"0"),+options =>
    S.bind(Nat,CLI.Options,D.natural(U32.read(bytes),16777216),n => Done{capacity(options,U32.from_nat(n))}))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{path,Nil{}}}:
      configured(source,path,Done{CLI.Options{D.Limits{65536n,512n,512n},4096n,4194304}})
    case Con{source,Con{path,Con{chars,Con{parser,Con{checker,Con{depth,Con{bytes,Nil{}}}}}}}}:
      configured(source,path,budgets(chars,parser,checker,depth,bytes))
    case _: D.fail(S.Host{"arguments","expected source output [characters parser-depth checker-depth emitter-depth output-bytes]"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
