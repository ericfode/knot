# A variable under a constructor names a field that an earlier row split.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

type Box is Type:
  Box{p: Pair}

def right(p: Pair) -> Flag:
  match p:
    case Pair{_, r}: r

def peek(x: Box) -> Flag:
  match x:
    case Box{Pair{On{}, _}}: Off{}
    case Box{q}: right(q)

def probe(a: Flag, b: Flag) -> Flag:
  peek(Box{Pair{a, b}})

def main() -> Flag:
  probe(Off{}, On{})
