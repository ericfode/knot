# Local module for io-do-imported: a statement-only do block whose last
# statement calls a module-local def.
import Base

def farewell(name: String) -> IO(Unit):
  IO.print(String.append("bye ",name))

def greet(+name: String) -> IO(Unit):
  do IO<Unit>:
    IO.print(String.append("hello ",name))
    farewell(name)
