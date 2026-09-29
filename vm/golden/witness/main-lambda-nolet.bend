import Base

def once(-R: Type, m: IO(Unit), n: IO(Unit), k: Unit -> IO.OP<R>) -> IO.OP<R>:
  n(R, k)

def main() -> IO(Unit):
  R => k => once(R, IO.print("dead"), IO.print("live"), k)
