type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  g = f()
  g(x)

def main() -> Flag:
  apply(invert, On{})
