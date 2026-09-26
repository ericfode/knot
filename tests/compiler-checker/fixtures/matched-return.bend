type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off{}: x
    case On{}: x

def main() -> Flag:
  f(On{})
