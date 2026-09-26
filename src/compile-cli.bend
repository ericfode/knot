import Base
import ./syntax.bend as S
import ./core.bend as C
import ./driver.bend as D
import ./wasm.bend as W

type Options is Data:
  Options{input: D.Limits, depth: Nat, bytes: U32}

def written(result: Result<&1,&1,U32 & String,Unit>, count: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\twrite\t",U32.show(code),"\t",message]))
    case Done{u}: IO.print(String.append("Built\t",U32.show(count)))

def write_pair(pair: File & Result<&1,&1,U32 & String,Unit>, count: U32) -> IO(Unit):
  (file,result) = pair
  do IO<Unit>:
    File.close(file)
    written(result,count)

def output_opened(result: Result<&1,&1,U32 & String,File>, +bytes: List<&2,U32>) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\toutput-open\t",U32.show(code),"\t",message]))
    case Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),pair => write_pair(pair,U32.from_nat(List.length(&2,U32,bytes))))

# Output is opened only after the complete module fits its byte budget.
def emitted(path: String, result: Result<S.Error,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+bytes}:
      IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),result => output_opened(result,bytes))

def compile(book: C.Book, path: String, options: Options) -> IO(Unit):
  match options:
    case Options{input,depth,bytes}: emitted(path,W.emit(book,depth,bytes))

def configured(+source: String, +path: String, result: Result<S.Error,Options>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+options}:
      match options:
        case Options{input,depth,bytes}:
          S.choose(IO(Unit),String.eq(source,path),u => D.fail(S.Host{"arguments","source-is-output"}),u =>
            D.load(source,input,book => compile(book,path,options)))

def budgets(chars: String, +parser: String, +checker: String, +depth: String, +bytes: String) -> Result<S.Error,Options>:
  S.bind(Nat,Options,D.natural(U32.read(chars),65536),c =>
    S.bind(Nat,Options,D.natural(U32.read(parser),4096),p =>
      S.bind(Nat,Options,D.natural(U32.read(checker),4096),k =>
        S.bind(Nat,Options,D.natural(U32.read(depth),4096),d =>
          S.bind(Nat,Options,D.natural(U32.read(bytes),1048576),b => Done{Options{D.Limits{c,p,k},d,U32.from_nat(b)}})))))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{path,Nil{}}}:
      configured(source,path,Done{Options{D.Limits{65536n,512n,512n},4096n,65536}})
    case Con{source,Con{path,Con{chars,Con{parser,Con{checker,Con{depth,Con{bytes,Nil{}}}}}}}}:
      configured(source,path,budgets(chars,parser,checker,depth,bytes))
    case _: D.fail(S.Host{"arguments","expected source output [characters parser-depth checker-depth emitter-depth output-bytes]"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
