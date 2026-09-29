type F is Data:
  F0{}
  F1{}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F, y: F) -> F:
  match x y:
    case F1{} _:
      + u : F = F1{}
      two(u, u)
    case _ _: F0{}

def main() -> F:
  f(F1{}, F1{})
