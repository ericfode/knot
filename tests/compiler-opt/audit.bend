import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/driver.bend as D
import ../../src/opt.bend as O
import ../../src/checked-display.bend as Display
import ../../src/eval-cli.bend as E

def repeat(rounds: Nat, book: C.Book) -> Result<S.Error,C.Book>:
  match rounds:
    case 0n: Done{book}
    case 1n+ +n: S.bind(C.Book,C.Book,O.pipeline(4096n,book),next => repeat(n,next))

def inspect(+mode: U32, +book: C.Book) -> IO(Unit):
  result = S.choose(Result<S.Error,C.Book>,U32.is_eq(mode,3),u => O.apply(4096n,O.Inline{},book),u =>
    S.choose(Result<S.Error,C.Book>,U32.is_eq(mode,4),u => O.apply(4096n,O.Fold{},book),u =>
      S.choose(Result<S.Error,C.Book>,U32.is_eq(mode,5),u => O.apply(4096n,O.Dead{},book),u => repeat(U32.to_nat(mode),book))))
  D.checked(result,next => E.print(Display.book(next)))

def configured(+path: String, mode: Maybe<&2,U32>) -> IO(Unit):
  match mode:
    case None{}: D.fail(S.Host{"arguments","expected-rounds"})
    case Some{+value}:
      S.choose(IO(Unit),U32.is_le(value,5),u => D.load(path,D.Limits{65536n,4096n,4096n},book => inspect(value,book)),u => D.fail(S.Host{"arguments","rounds-out-of-range"}))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Con{rounds,Nil{}}}: configured(path,U32.read(rounds))
    case _: D.fail(S.Host{"arguments","expected source rounds (0..2) or pass (3..5)"})

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
