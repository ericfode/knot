import Base

type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case _: On{}

def main() -> Flag:
  f(Off{})
