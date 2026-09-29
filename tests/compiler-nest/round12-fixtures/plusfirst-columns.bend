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

def f(p: Pair, q: Flag) -> Flag:
  match p q:
    case P{On{}, +v} _: v
    case P{Off{}, v} _: both(v, v)

def probe(a: Flag, b: Flag, c: Flag) -> Flag:
  f(P{a, b}, c)

def main() -> Flag:
  probe(On{}, Off{}, On{})
