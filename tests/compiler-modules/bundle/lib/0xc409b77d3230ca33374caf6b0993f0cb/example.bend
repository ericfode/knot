import Base
import ./main.bend as Text
import ./bytes.bend as Bytes

def byte_example(result: Result<Bytes.Error,Bytes.Builder>) -> IO(Unit):
  match result:
    case Fail{err}:
      IO.die(Unit,1,"byte example failed")
    case Done{+b}:
      do IO<Unit>:
        IO.print(U32.show(Bytes.length(b)))
        IO.print(Bool.show(List.is_empty(&2,U32,Bytes.finish(b))))

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(Text.finish(Text.character(Text.compose(Text.fragment("hello"),Text.fragment(" λ🙂")),Chr{10})))
    byte_example(Bytes.fragment(8,[0,97,115,109,1,0,0,0]))
