import Base

# An IO value is a description: it runs where it is bound, never where it is built.
def later(action: IO(Unit)) -> IO(Unit):
  do IO<Unit>:
    IO.print("before the action")
    action

def branch(flag: Bool, yes: IO(Unit), no: IO(Unit)) -> IO(Unit):
  match flag:
    case True{}: yes
    case False{}: no

def main() -> IO(Unit):
  unused = IO.print("never built into the program")
  do IO<Unit>:
    later(IO.print("the action"))
    branch(True{},IO.print("chosen"),IO.print("not chosen"))
    branch(False{},IO.print("not chosen"),IO.print("chosen too"))
