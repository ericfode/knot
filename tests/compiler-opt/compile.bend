import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/compile-cli.bend as CLI
import ../../src/opt-wasm.bend as W
import ../../src/opt.bend as O

def compile(book: C.Book, path: String, options: CLI.Options) -> IO(Unit):
  match options:
    case CLI.Options{input,+depth,bytes}:
      CLI.emitted(path,S.bind(C.Book,List<&2,U32>,O.pipeline(depth,book),optimized => W.emit(optimized,depth,bytes)))

def configured(+source: String, +path: String, result: Result<S.Error,CLI.Options>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+options}:
      match options:
        case CLI.Options{input,depth,bytes}:
          S.choose(IO(Unit),String.eq(source,path),u => D.fail(S.Host{"arguments","source-is-output"}),u =>
            D.load(source,input,book => compile(book,path,options)))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{source,Con{path,Nil{}}}:
      configured(source,path,Done{CLI.Options{D.Limits{65536n,512n,512n},4096n,65536}})
    case Con{source,Con{path,Con{chars,Con{parser,Con{checker,Con{depth,Con{bytes,Nil{}}}}}}}}:
      configured(source,path,CLI.budgets(chars,parser,checker,depth,bytes))
    case _: D.fail(S.Host{"arguments","expected source output [characters parser-depth checker-depth emitter-depth output-bytes]"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
