type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  P{l: Flag, r: Flag}

def g(p: Pair) -> Flag:
  match p:
    case P{a, b}: b

def f(a: Flag) -> Flag:
  g(P{a,
    On{}})
