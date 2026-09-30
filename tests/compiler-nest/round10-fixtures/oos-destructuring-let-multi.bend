type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F, p: P) -> F:
  match x p:
    case F0{} _:
      F0{}
    case F1{} q:
      Pr{c, d} = q
      two(c, d)

def main() -> F:
  f(F1{}, Pr{F1{}, F1{}})
