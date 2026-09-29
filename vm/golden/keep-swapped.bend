import Base

def keep(-R: Type, x: IO.OP<R>, y: IO.OP<R>) -> IO.OP<R>:
  y

def run2(m1: IO(Unit), m2: IO(Unit)) -> IO(Unit):
  R => k => keep(R, m1(R, x => Halt{7, "unreached"}), m2(R, k))

def main() -> IO(Unit):
  run2(IO.print("dropped"), IO.print("kept"))
