import Base
import ../../src/syntax.bend as S
import ../../src/diagnostic.bend as D
import ../../src/base-pin.bend as H
import ../../src/load.bend as L

def printed(result: Result<S.Error,String>) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,D.status(error),D.error(error))
    case Done{text}: IO.print(text)

def verified(result: Result<S.Error,String>) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,D.status(error),D.error(error))
    case Done{text}: IO.print("Verified")

def observe(result: Result<S.Error,String>, +verify: Bool) -> IO(Unit):
  match result:
    case Fail{+error}: IO.die(Unit,D.status(error),D.error(error))
    case Done{+text}:
      S.choose(IO(Unit),verify,u => verified(H.verify(text)),u => printed(H.hash(text)))

def arguments(args: List<String>) -> IO(Unit):
  match args:
    case Con{path,Nil{}}: L.read(path,131073,False{},result => observe(result,False{}))
    case Con{flag,Con{+path,Nil{}}}:
      S.choose(IO(Unit),String.eq(flag,"--verify"),u => L.read(path,131073,False{},result => observe(result,True{})),u =>
        IO.die(Unit,5,"HostFailure\targuments\texpected [--verify] path"))
    case _: IO.die(Unit,5,"HostFailure\targuments\texpected [--verify] path")

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),arguments)
