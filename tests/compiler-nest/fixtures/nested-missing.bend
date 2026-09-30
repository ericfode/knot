# A nested match that omits the leaf pair Box{Pair{On{}, Off{}}}.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

type Box is Type:
  Box{p: Pair}

def open(x: Box) -> Flag:
  match x:
    case Box{Pair{On{}, On{}}}: Off{}
    case Box{Pair{Off{}, v}}: v

def main() -> Flag:
  open(Box{Pair{On{}, On{}}})
