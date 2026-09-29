type C3 is Data:
  A{}
  B{}
  C{}

type Box is Type:
  K{c: C3}

type Two is Type:
  T{a: C3, b: Box}

def g(x: Box) -> C3:
  match x:
    case K{c}: c

def f(x: Two) -> C3:
  match x:
    case T{A{}, K{B{}}}: A{}
    case T{a, k}:
      +v = k
      g(v)

def main() -> C3:
  A{}
