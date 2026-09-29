import Base

def once(-R: Type, m: IO(Unit), n: IO(Unit), k: Unit -> IO.OP<R>) -> IO.OP<R>:
  dead : IO.OP<R> = m(R, x => Halt{7, "unreached"})
  live : IO.OP<R> = n(R, k)
  live

def run(m: IO(Unit), n: IO(Unit)) -> IO(Unit):
  R => k => once(R, m, n, k)

def main() -> IO(Unit):
  run(IO.print("dead"), IO.print("live"))
