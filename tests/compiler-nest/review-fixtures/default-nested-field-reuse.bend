# A nested field binder reaches the default region of its own column and is used twice.
type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  Pair{l: Flag, r: Flag}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(p: Pair) -> Flag:
  match p:
    case Pair{Off{}, _}: Off{}
    case Pair{v, _}: both(v, v)

def probe(a: Flag, b: Flag) -> Flag:
  f(Pair{a, b})

def main() -> Flag:
  probe(On{}, Off{})
