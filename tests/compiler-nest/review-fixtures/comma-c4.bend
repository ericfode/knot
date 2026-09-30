type Flag is Data:
  Off{}
  On{}

def f(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{},: Off{}

def main() -> Flag:
  f(On{}, On{})
