type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag, y: Flag) -> Flag:
  match x y:
    case Off{} Off{}:
      v = x
      - y
      v
    case _ _: On{}

def main() -> Flag:
  f(On{}, Off{})
