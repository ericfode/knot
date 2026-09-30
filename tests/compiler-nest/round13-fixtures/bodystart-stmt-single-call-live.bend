type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(a: Flag) -> Flag:
  match a:
    case Off{}: a
    case On{}:
      u : Flag = a
  (k(a))

def main() -> Flag:
  f(On{})
