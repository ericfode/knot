# Knot-specific: a nested pattern through a parameterized datatype, outside this stage.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

type Box<-A: Type> is Type:
  Box{v: A}

def open(x: Box<Pair>) -> Flag:
  match x:
    case Box{Pair{On{}, r}}: r
    case Box{Pair{Off{}, _}}: Off{}

def probe(a: Flag, b: Flag) -> Flag:
  open(Box{Pair{a, b}})

def main() -> Flag:
  probe(On{}, On{})
