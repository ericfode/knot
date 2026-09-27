import Base
import ../../src/syntax.bend as S
import ../../src/diagnostic.bend as D
import ./module.bend as M

def show(result: Result<S.Error,List<&2,U32>>) -> String:
  match result:
    case Fail{error}: D.error(error)
    case Done{bytes}: List.show(~&2,~U32,~U32.show,bytes)

def main() -> IO(Unit):
  IO.print(show(M.emit(65536)))
