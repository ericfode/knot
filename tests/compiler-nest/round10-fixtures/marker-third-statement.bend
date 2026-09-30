type F is Data:
  F0{}
  F1{}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F) -> F:
  v = x
  w : F = v
  + u = w
  two(u, u)

def main() -> F:
  f(F1{})
