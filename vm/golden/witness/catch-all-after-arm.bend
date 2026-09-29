import Base

type Flag is Data:
  Off{}
  On{}

def h(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case _: Off{}

def main() -> Flag:
  h(Off{})
