import Base

def cap(-R: Type, r: IO.OP<R>) -> Unit -> IO.OP<R>:
  x => r

def pick2(-R: Type, f: Unit -> IO.OP<R>, g: Unit -> IO.OP<R>) -> Unit -> IO.OP<R>:
  g

def run(m: IO(Unit), n: IO(Unit)) -> IO(Unit):
  R => k => n(R, pick2(R, cap(R, m(R, x => Halt{7, "unreached"})), k))

def main() -> IO(Unit):
  run(IO.print("captured-dropped"), IO.print("live"))
