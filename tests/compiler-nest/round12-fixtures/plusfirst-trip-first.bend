type Flag is Data:
  Off{}
  On{}

type Pair is Type:
  P{l: Flag, r: Flag}

type Trip is Type:
  T3{a: Flag, b: Flag, c: Flag}

type Box is Type:
  Bx{p: Pair}

type Two is Type:
  A{x: Flag, y: Flag}
  B{x: Flag, y: Flag}

type Data2 is Data:
  D2{l: Flag, r: Flag}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(p: Trip) -> Flag:
  match p:
    case T3{+a, On{}, On{}}: a
    case T3{a, b, c}: both(a, both(a, b))
    case T3{_, _, _}: Off{}

def probe(a: Flag, b: Flag, c: Flag) -> Flag:
  f(T3{a, b, c})

def main() -> Flag:
  probe(On{}, Off{}, On{})
