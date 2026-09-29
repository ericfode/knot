import Base

def run2(m1: IO(Unit), m2: IO(Unit)) -> IO(Unit):
  R => k => m1(R, x => m2(R, k))

def main() -> IO(Unit):
  run2(IO.print("first"), IO.print("second"))
