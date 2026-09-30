# Rebuilding a nested alias preserves the affine obligation of its live field.
type Flag is Data:
  Off{}
  On{}
type Pair is Type:
  Pair{left: Flag, right: Flag}
type Box is Type:
  Box{pair: Pair}

def right(p: Pair) -> Flag:
  match p:
    case Pair{_, r}: r

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case Off{}: b
    case On{}: On{}

def read(x: Box) -> Flag:
  match x:
    case Box{Pair{On{}, _}}: Off{}
    case Box{p}: both(right(p), right(p))

def main() -> Flag:
  read(Box{Pair{Off{}, On{}}})
