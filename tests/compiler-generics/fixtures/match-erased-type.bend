# A match on an erased type parameter with only a variable arm inspects nothing.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def inspect(-A: Type, x: Flag) -> Flag:
  match A:
    case T:
      x

def run(x: Flag) -> Flag:
  inspect(Color, x)

def main() -> Flag:
  run(Off{})
