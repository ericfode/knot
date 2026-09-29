type F is Data:
  F0{}
  F1{}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def id(a: F)-> F:
  a

def main() -> F:
  id(F1{})
