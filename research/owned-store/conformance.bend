import Base
import ./store.bend as S
import ./protocol.bend as P
import ./observe.bend as O
import ./model.bend as M

def check(test: P.Case) -> String:
  match test:
    case P.Case{id,+arena,+capacity,+ceiling,+commands}:
      String.join([U32.show(id),O.start(S.new(O.Payload,arena,capacity,ceiling),commands),
        M.start(arena,capacity,ceiling,commands)],"|")

def run(cases: List<&2,P.Case>) -> IO(Unit):
  match cases:
    case Nil{}: IO.pure(Unit,Unit{})
    case Con{head,tail}:
      do IO<Unit>:
        IO.print(check(head))
        run(tail)
