type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(a: F, c: F) -> F:
  match a:
    case ++y: two(y, y)
    case _: F0{}

def main() -> F:
  F0{}
