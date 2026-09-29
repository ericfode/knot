import Base

type Flag is Data:
  Off{}
  On{}

def keep(-R: Type, x: IO.OP<R>, y: Flag) -> Flag:
  y

def go(m: IO(Unit)) -> Flag:
  keep(Flag, m(Flag, u => Emit{On{}}), On{})

def main() -> Flag:
  go(IO.print("x"))
