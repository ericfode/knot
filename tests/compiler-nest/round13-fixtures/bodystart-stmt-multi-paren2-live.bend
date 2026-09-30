type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case On{} x: a
    case Off{} y:
      u : Flag = y
  ((a))

def main() -> Flag:
  f(On{}, Off{})
