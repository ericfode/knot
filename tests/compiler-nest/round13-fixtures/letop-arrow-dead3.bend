type Flag is Data:
  Off{}
  On{}

def h(a: Flag, b: Flag) -> Flag:
  a

def k(a: Flag) -> Flag:
  a

def f(x: Flag, y: Flag, z: Flag) -> Flag:
  match x y z:
    case _ _ _: On{}
    case Off{} Off{} Off{}:
      v = x
      -> y
      v

def main() -> Flag:
  f(On{}, Off{}, Off{})
