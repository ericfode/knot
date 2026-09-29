type F is Data:
  F0{}
  F1{}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F) -> F:
  match x:
    case +++y: two(y, y)

def main() -> F:
  f(F1{})
