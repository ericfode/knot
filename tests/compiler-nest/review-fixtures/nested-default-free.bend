# A nested wildcard row after complete nested constructor rows names an unbound variable.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

def f(p: Pair) -> Flag:
  match p:
    case Pair{On{}, _}: On{}
    case Pair{Off{}, _}: Off{}
    case Pair{_, _}: nope

def probe(a: Flag, b: Flag) -> Flag:
  f(Pair{a, b})

def main() -> Flag:
  probe(On{}, Off{})
