type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(a: Flag) -> Flag:
  match a:
    case On{}: a
    case Off{}:
    ((a))

def main() -> Flag:
  f(On{})
