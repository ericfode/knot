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

def f(p: Pair) -> Flag:
  match p:
    case P{+a, On{}}: a
    case P{a, Off{}}: both(a, a)

def probe(a: Flag, b: Flag) -> Flag:
  f(P{a, b})

def main() -> Flag:
  probe(On{}, Off{})
