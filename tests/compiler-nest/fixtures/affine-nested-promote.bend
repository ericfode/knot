# A + mark two constructors deep promotes a Data field inside a Type parent.
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
    case Box{Pair{+a, b}}: both(a, a)

def probe(a: Flag, b: Flag) -> Flag:
  left(Box{Pair{a, b}})

def main() -> Flag:
  probe(On{}, Off{})
