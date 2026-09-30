type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F) -> F:
  w =
  x
  w

def main() -> F:
  f(F1{})
