type Flag is Data:
  Off{}
  On{}

def f(x: Flag, y: Flag) -> Flag:
  match x:
    case
      On{}: y
    case Off{}: Off{}

def main() -> Flag:
  f(On{}, On{})
