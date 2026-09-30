type C3 is Data:
  A{}
  B{}
  C{}

type Flag is Data:
  Off{}
  On{}

type TS is Data:
  SL{}
  SU{}
  SW{}

type T is Type:
  L{}
  U{a: C3}
  W{a: C3, b: C3}

type Pair is Type:
  P{l: T, r: C3}

def mkT(s: TS, a: C3, b: C3) -> T:
  match s:
    case SL{}: L{}
    case SU{}: U{a}
    case SW{}: W{a, b}

def gT(t: T) -> C3:
  match t:
    case L{}: C{}
    case U{a}: a
    case W{a, b}: b

def hP(p: Pair) -> C3:
  match p:
    case P{t, r}: gT(t)

def two(s: T, t: T) -> C3:
  gT(s)

def pick(a: C3, b: C3) -> C3:
  match a:
    case A{}: b
    case _: a

def f(x: Pair, y: T, z: C3) -> C3:
  match y:
    case W{B{}, B{}}: z
    case _:
      v0 = y
      B{}

def probe(s: TS, a: C3, b: C3, r: C3, t: TS, c: C3, d: C3, z: C3) -> C3:
  f(P{mkT(s, a, b), r}, mkT(t, c, d), z)

def main() -> C3:
  probe(SW{}, B{}, C{}, A{}, SU{}, B{}, C{}, A{})
