type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case _ _: On{}
    case Off{} Off{}:
      v = x
      >> y
      v

def main() -> Flag:
  f(On{}, Off{})
