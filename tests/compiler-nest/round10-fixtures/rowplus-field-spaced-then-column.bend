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
    case Pr{l, + r} d: two(r, d)
    case _ _: F0{}

def main() -> F:
  f(Pr{F1{}, F1{}}, F1{})
