import Base

type Flag is Data:
  Off{}
  On{}

def got(-R: Type, x: IO.OP<R>) -> Flag:
  match x:
    case Emit{v}: Off{}
    case Halt{c, m}: Off{}
    case _: On{}

def go(m: IO(Unit)) -> Flag:
  got(Flag, m(Flag, u => Emit{On{}}))

def main() -> Flag:
  go(IO.print("x"))
