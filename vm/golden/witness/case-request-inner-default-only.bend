import Base

def got(-R: Type, x: IO.OP<R>, d: U32) -> U32:
  match x:
    case Emit{v}: 1
    case Halt{c, m}:
      match c:
        case 0: 2
        case _: 3

def run(m: IO(Unit)) -> IO(Unit):
  R => k => IO.print(U32.show(got(R, m(R, x => Halt{7, "unreached"}), 0)))(R, k)

def main() -> IO(Unit):
  run(IO.print("x"))
