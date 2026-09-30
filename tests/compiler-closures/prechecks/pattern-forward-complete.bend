def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def main() -> Flag:
  invert(Off{})

type Flag is Data:
  Off{}
  On{}
