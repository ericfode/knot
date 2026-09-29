import Base

def got(-R: Type, x: IO.OP<R>, d: Unit) -> Unit:
  match x:
    case Emit{v}: d
    case _: d

def run(m: IO(Unit)) -> IO(Unit):
  R => k => k(got(R, m(R, x => Halt{7, "unreached"}), Unit{}))

def main() -> IO(Unit):
  run(IO.print("x"))
