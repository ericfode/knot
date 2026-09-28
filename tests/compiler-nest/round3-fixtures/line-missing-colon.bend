type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case On{}
    case Off{}: Off{}

def main() -> Flag:
  f(On{})
