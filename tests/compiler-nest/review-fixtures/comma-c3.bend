type Flag is Data:
  Off{}
  On{}

def f(a: Flag, b: Flag) -> Flag:
  match a, b:
    case On{}, On{}: On{}
    case _, _: Off{}

def main() -> Flag:
  f(On{}, On{})
