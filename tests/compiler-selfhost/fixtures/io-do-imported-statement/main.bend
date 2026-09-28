# Twin of io-do-imported: the imported module's do block opens with a String statement.
import Base
import ./lib.bend as L

def each(names: List<String>) -> IO(Unit):
  match names:
    case Nil{}: IO.print("none")
    case Con{name,Nil{}}: L.greet(name)
    case Con{name,rest}: IO.bind(Unit,Unit,L.greet(name),u => each(rest))

def main() -> IO(Unit):
  IO.bind(List<String>,Unit,IO.args(),each)
