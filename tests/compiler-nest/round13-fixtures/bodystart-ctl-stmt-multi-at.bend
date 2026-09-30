type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(a: Flag, b: Flag) -> Flag:
  match a b:
    case x y: x
    case On{} z:
      u : Flag = z
  @a

def main() -> Flag:
  f(On{}, Off{})
