import Base

def got(-R: Type, x: IO.OP<R>) -> U32:
  match x:
    case Halt{c, m}: 3
    case _: 4

def run(m: IO(Unit)) -> IO(Unit):
  R => k => IO.print(U32.show(got(R, m(R, x => Halt{7, "unreached"}))))(R, k)

def main() -> IO(Unit):
  run(IO.print("x"))
