import Base

# IO.die ends the program: neither its continuation nor any later effect runs.
def main() -> IO(Unit):
  do IO<Unit>:
    IO.print("one")
    IO.bind(String,Unit,IO.die(String,4,"halt"),text => IO.print(text))
    IO.print("never")
