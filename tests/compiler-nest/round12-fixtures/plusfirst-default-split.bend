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

def f(t: Two) -> Flag:
  match t:
    case A{On{}, +y}: y
    case B{Off{}, +z}: z
    case A{Off{}, y}: both(y, y)
    case B{On{}, z}: both(z, z)

def probe(a: Flag, b: Flag, k: Flag) -> Flag:
  match k:
    case On{}: f(A{a, b})
    case Off{}: f(B{a, b})

def main() -> Flag:
  probe(On{}, Off{}, On{})
