# A + binder needs a Data type, and every function type is Type.
type Flag is Data:
  Off{}
  On{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def twice(+f: Flag -> Flag, x: Flag) -> Flag:
  f(f(x))

def main() -> Flag:
  twice(invert, On{})
