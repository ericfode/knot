# A wildcard after complete constructor rows reuses an affine parameter.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(x: Flag, y: Flag) -> Flag:
  match x:
    case On{}: y
    case Off{}: y
    case _: both(y, y)

def main() -> Flag:
  f(On{}, Off{})
