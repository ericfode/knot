type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def eat(-v: Flag, x: Flag) -> Flag:
  x

def app(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def main() -> Flag -> Flag:
  invert
