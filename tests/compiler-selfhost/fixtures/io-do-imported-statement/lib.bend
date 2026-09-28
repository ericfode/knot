# Local module for io-do-imported-statement: a do statement that is not an IO action.
import Base

def farewell(name: String) -> IO(Unit):
  IO.print(String.append("bye ",name))

def greet(+name: String) -> IO(Unit):
  do IO<Unit>:
    String.append("hello ",name)
    farewell(name)
