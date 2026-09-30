type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(p: P, c: F) -> F:
  match p c:
    case Pr{l, r} +d: two(l, d)
    case _ _: F0{}

def probe(a: F, b: F, c: F) -> F:
  f(Pr{a, b}, c)

def main() -> F:
  probe(F1{}, F0{}, F1{})
