import Base

def keep(-R: Type, x: IO.OP<R>, y: IO.OP<R>) -> IO.OP<R>:
  x

def run2(m1: IO(Unit), m2: IO(Unit)) -> IO(Unit):
  R => k => keep(R, m1(R, k), m2(R, x => Halt{7, "unreached"}))

def main() -> IO(Unit):
  run2(IO.print("kept"), IO.print("dropped"))
