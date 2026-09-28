import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/compile-cli.bend as CLI
import ../../src/records.bend as R

def configured(+source: String, +path: String, +name: String, +depth: Nat, +bytes: U32, result: Result<S.Error,List<&2,U32>>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{+args}:
      S.choose(IO(Unit),String.eq(source,path),u => D.fail(S.Host{"arguments","source-is-output"}),u =>
        D.load(source,D.Limits{65536n,512n,512n},book => CLI.emitted(path,R.emit(book,name,args,depth,bytes))))

def arguments(args: List<String>, depth: Nat, bytes: U32) -> IO(Unit):
  match args:
    case Con{source,Con{path,Con{name,values}}}:
      configured(source,path,name,depth,bytes,D.ordinals(values))
    case _: D.fail(S.Host{"arguments","expected source output entry [live-ordinals...]"})

def byte_budget(args: List<String>, depth: Nat, result: Result<S.Error,Nat>) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{bytes}: arguments(args,depth,U32.from_nat(bytes))

def budgets(args: List<String>, result: Result<S.Error,Nat>, +raw: String) -> IO(Unit):
  match result:
    case Fail{e}: D.fail(e)
    case Done{depth}: byte_budget(args,depth,D.natural(U32.read(raw),1048576))

def limited(args: List<String>) -> IO(Unit):
  match args:
    case Con{depth,Con{bytes,rest}}: budgets(rest,D.natural(U32.read(depth),4096),bytes)
    case _: D.fail(S.Host{"arguments","expected --limits depth bytes source output entry [live-ordinals...]"})

def option(selected: Bool, head: String, tail: List<String>) -> IO(Unit):
  match selected:
    case True{}: limited(tail)
    case False{}: arguments(Con{head,tail},4096n,1048576)

def options(args: List<String>) -> IO(Unit):
  match args:
    case Con{+head,tail}: option(String.eq(head,"--limits"),head,tail)
    case Nil{}: arguments(Nil{},4096n,1048576)

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),options)
