type Flag is Data:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case On.x: On{}

def main() -> Flag:
  f(On{})
