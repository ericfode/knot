type F is Data:
  F0{}
  F1{}

type P is Type:
  Pr{l: F, r: F}

def two(a: F, b: F) -> F:
  match a:
    case F1{}: b
    case F0{}: F0{}

type Box<-A: Type> is Type:
  Box{v: A}

def f(b: Box<F>, y: F) -> F:
  match b y:
    case Box{v} _: v

def main() -> F:
  f(Box{F0{}}, F1{})
