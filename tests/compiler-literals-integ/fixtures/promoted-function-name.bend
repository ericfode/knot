# A function's name is no type: a promoted binder may repeat it.
type Flag is Data:
  Off{}
  On{}

def g(x: Flag) -> Flag:
  x

def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case +g: Off{}

def main() -> Flag:
  f(On{})
