import Base

type Flag is Data:
  Off{}
  On{}

def pick(-R: Type, b: Flag, x: IO.OP<R>, y: IO.OP<R>) -> IO.OP<R>:
  match b:
    case On{}:
      x
    case Off{}:
      y

def run2(m1: IO(Unit), m2: IO(Unit)) -> IO(Unit):
  R => k => pick(R, On{}, m1(R, k), m2(R, x => Halt{7, "unreached"}))

def main() -> IO(Unit):
  run2(IO.print("first"), IO.print("second"))
