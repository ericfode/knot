type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case a.1: On{}

def main() -> Flag:
  f(On{})
