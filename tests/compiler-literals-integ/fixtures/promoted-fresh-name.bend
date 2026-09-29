# A promoted binder with a fresh name: nothing to read as a type.
type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case +z: Off{}

def main() -> Flag:
  f(On{})
