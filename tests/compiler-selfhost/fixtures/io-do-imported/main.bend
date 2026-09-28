# A statement-only `do IO<Unit>:` in an imported module (SF-14), reached from the entry.
import Base
import ./lib.bend as L

def each(names: List<String>) -> IO(Unit):
  match names:
    case Nil{}: IO.print("none")
    case Con{name,Nil{}}: L.greet(name)
    case Con{name,rest}: IO.bind(Unit,Unit,L.greet(name),u => each(rest))

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),each)
