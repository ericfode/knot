import Base
import ./syntax.bend as S
import ./core.bend as C
import ./driver.bend as D
import ./wasm.bend as W
import ./image.bend as I

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

def plain_arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{path,Nil{}}}:
      configured(source,path,Done{Options{D.Limits{65536n,512n,512n},4096n,65536}})
    case Con{source,Con{path,Con{chars,Con{parser,Con{checker,Con{depth,Con{bytes,Nil{}}}}}}}}:
      configured(source,path,budgets(chars,parser,checker,depth,bytes))
    case _: D.fail(S.Host{"arguments","expected source output [characters parser-depth checker-depth emitter-depth output-bytes]"})

# --profile=knot-image-1 selects the image profile explicitly. It reads and writes at its own budgets
# (vm/SPEC.md section 4 bounds an image at 4,194,304 words), streams the image in chunks and opens the
# output only after the whole image is laid out and fits, as the default profile does.
def image_closed(file: File, +count: U32) -> IO(Unit):
  do IO<Unit>:
    File.close(file)
    IO.print(String.append("Built\t",U32.show(count)))

def image_failed(file: File, code: U32, message: String) -> IO(Unit):
  do IO<Unit>:
    File.close(file)
    IO.die(Unit,5,String.concat(["HostFailure\twrite\t",U32.show(code),"\t",message]))

# Each chunk costs three steps of the fuel: an image has at most 4,194,304 words, so a million steps
# cover every image the profile can write. The file handle is affine, so the modes are a Type.
type Write is Type:
  Next{file: File, step: I.Step, count: U32}
  Pair{pair: File & Result<&1,&1,U32 & String,Unit>, rest: I.Cursor, count: U32}
  Sent{file: File, result: Result<&1,&1,U32 & String,Unit>, rest: I.Cursor, count: U32}

def image_write(fuel: Nat, mode: Write) -> IO(Unit):
  match fuel mode:
    case 0n _: IO.die(Unit,6,"InternalFailure\tcompile\timage-chunks")
    case 1n+ +n Next{file,I.End{},+count}: image_closed(file,count)
    case 1n+ +n Next{file,I.Chunk{bytes,rest},count}:
      IO.bind(File & Result<&1,&1,U32 & String,Unit>,Unit,File.write_bytes(file,bytes),pair => image_write(n,Pair{pair,rest,count}))
    case 1n+ +n Pair{pair,rest,count}:
      (file,result) = pair
      image_write(n,Sent{file,result,rest,count})
    case 1n+ +n Sent{file,Fail{(code,message)},rest,count}: image_failed(file,code,message)
    case 1n+ +n Sent{file,Done{u},rest,count}: image_write(n,Next{file,I.pull(rest),count})

def image_opened(result: Result<&1,&1,U32 & String,File>, encoded: I.Encoded, +count: U32) -> IO(Unit):
  match result:
    case Fail{(code,message)}: IO.die(Unit,5,String.concat(["HostFailure\toutput-open\t",U32.show(code),"\t",message]))
    case Done{file}: image_write(1000000n,Next{file,I.pull(I.start(encoded)),count})

def image_written(path: String, encoded: I.Encoded, +count: U32) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"w"),result => image_opened(result,encoded,count))

# The size is checked in words before it is multiplied: the output budget is at most 16,777,216 bytes.
def image_sized(path: String, encoded: I.Encoded, +cap: U32) -> IO(Unit):
  match encoded:
    case I.Encoded{records,+words}:
      S.choose(IO(Unit),U32.is_le(words,U32.shrn(cap,2n)),u => image_written(path,I.Encoded{records,words},U32.mul(words,4)),u => D.fail(S.Exhausted{"compile",S.At{0,0,0,0}}))

def image_emitted(path: String, result: Result<S.Error,I.Encoded>, +cap: U32) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{encoded}: image_sized(path,encoded,cap)

def image_compile(book: C.Book, path: String, options: Options) -> IO(Unit):
  match options:
    case Options{input,depth,bytes}: image_emitted(path,I.encode(depth,book),bytes)

# The default loader reads 65,537 characters. The image profile reads its own budget plus one, so a
# source over the budget is exhausted by the lexer and one at the budget is admitted.
def image_read(limits: D.Limits, result: Result<&1,&1,U32 & String,File>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits result:
    case D.Limits{characters,parser,checker} Fail{(code,message)}:
      IO.die(Unit,5,String.concat(["HostFailure\topen\t",U32.show(code),"\t",message]))
    case D.Limits{+characters,parser,checker} Done{file}:
      IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(file,U32.add(U32.from_nat(characters),1)),pair => D.read_pair(D.Limits{characters,parser,checker},pair,next))

def image_load(path: String, limits: D.Limits, next: C.Book -> IO(Unit)) -> IO(Unit):
  IO.bind(Result<&1,&1,U32 & String,File>,Unit,File.open(path,"r"),result => image_read(limits,result,next))

def image_configured(+source: String, +path: String, result: Result<S.Error,Options>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+options}:
      match options:
        case Options{input,depth,bytes}:
          S.choose(IO(Unit),String.eq(source,path),u => D.fail(S.Host{"arguments","source-is-output"}),u =>
            image_load(source,input,book => image_compile(book,path,options)))

def image_budgets(chars: String, +parser: String, +checker: String, +depth: String, +bytes: String) -> Result<S.Error,Options>:
  S.bind(Nat,Options,D.natural(U32.read(chars),4194304),c =>
    S.bind(Nat,Options,D.natural(U32.read(parser),4096),p =>
      S.bind(Nat,Options,D.natural(U32.read(checker),4096),k =>
        S.bind(Nat,Options,D.natural(U32.read(depth),1048576),d =>
          S.bind(Nat,Options,D.natural(U32.read(bytes),16777216),b => Done{Options{D.Limits{c,p,k},d,U32.from_nat(b)}})))))

def image_arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{path,Nil{}}}:
      image_configured(source,path,Done{Options{D.Limits{1048576n,512n,512n},1048576n,16777216}})
    case Con{source,Con{path,Con{chars,Con{parser,Con{checker,Con{depth,Con{bytes,Nil{}}}}}}}}:
      image_configured(source,path,image_budgets(chars,parser,checker,depth,bytes))
    case _: D.fail(S.Host{"arguments","expected --profile=knot-image-1 source output [characters parser-depth checker-depth emitter-depth output-bytes]"})

def prefixed(prefix: String, text: String) -> Bool:
  match prefix text:
    case SNil{} _: True{}
    case SCon{a,+rest} SCon{b,+more}: Bool.and(Char.is_eq(a,b),prefixed(rest,more))
    case SCon{a,rest} SNil{}: False{}

def chosen(image: Bool, unknown: Bool, flag: String, rest: List<String>) -> IO(Unit):
  match image unknown:
    case True{} _: image_arguments(rest)
    case False{} True{}: D.fail(S.Host{"arguments","unknown-profile"})
    case False{} False{}: plain_arguments(Con{flag,rest})

def selected(+flag: String, rest: List<String>) -> IO(Unit):
  chosen(String.eq(flag,"--profile=knot-image-1"),prefixed("--profile=",flag),flag,rest)

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{flag,rest}: selected(flag,rest)
    case Nil{}: plain_arguments(Nil{})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
