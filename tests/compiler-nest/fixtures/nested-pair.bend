# A pattern two constructors deep; specific and variable rows cover every leaf pair.
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
    case Box{Pair{On{}, Off{}}}: On{}

def xor(a: Flag, b: Flag) -> Flag:
  open(Box{Pair{a, b}})

def main() -> Flag:
  xor(On{}, Off{})
