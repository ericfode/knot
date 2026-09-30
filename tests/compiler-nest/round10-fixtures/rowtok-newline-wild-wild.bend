type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F, y: F) -> F:
  match x y:
    case _
      + _: F1{}
    case _ _: F0{}

def main() -> F:
  f(F1{}, F1{})
