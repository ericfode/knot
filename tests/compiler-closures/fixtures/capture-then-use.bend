# An affine parameter captured by a lambda cannot be used again after the capture.
type Flag is Data:
  Off{}
  On{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: Off{}
    case On{}: b

def annotated(k: Flag, x: Flag) -> Flag:
  g : Flag -> Flag = y => both(y, k)
  both(g(x), k)

def main() -> Flag:
  annotated(On{}, On{})
