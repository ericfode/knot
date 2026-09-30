# An affine field bound two constructors deep is used twice.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

type Box is Type:
  Box{p: Pair}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def left(x: Box) -> Flag:
  match x:
    case Box{Pair{a, b}}: both(a, a)

def main() -> Flag:
  left(Box{Pair{On{}, Off{}}})
