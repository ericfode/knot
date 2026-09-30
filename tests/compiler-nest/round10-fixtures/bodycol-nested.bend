type F is Data:
  F0{}
  F1{}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(x: F, y: F) -> F:
  match x:
    case F0{}:
      match y:
      case F0{}:
      F1{}
      case F1{}: F0{}
    case F1{}: F0{}

def main() -> F:
  f(F1{}, F1{})
