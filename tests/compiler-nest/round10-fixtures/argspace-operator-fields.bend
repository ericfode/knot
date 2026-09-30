type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

def f(p: P) -> F:
  match p:
    case Pr{a + b}: two(a, b)

def main() -> F:
  f(Pr{F1{}, F1{}})
