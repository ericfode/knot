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
  match p:
    case Pr{a b}: two(a, b)
    case _: F0{}

def main() -> F:
  F0{}
