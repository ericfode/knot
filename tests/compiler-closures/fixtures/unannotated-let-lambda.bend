# A let-bound lambda without a type annotation; the seed cannot infer it.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def annotated(k: Flag, x: Flag) -> Flag:
  g = y => both(y, k)
  g(x)

def main() -> Flag:
  annotated(On{}, On{})
