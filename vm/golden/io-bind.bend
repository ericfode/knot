import Base

def main() -> IO(Unit):
  IO.bind(Unit,Unit,IO.print("a"),x => IO.bind(Unit,Unit,IO.pure(Unit,x),y => IO.print("b")))
