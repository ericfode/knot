type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case a.b: a.b

def main() -> Flag:
  f(On{})
