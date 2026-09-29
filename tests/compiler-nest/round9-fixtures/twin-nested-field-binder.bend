type C3 is Data:
  A{}
  B{}

type Box is Type:
  K{c: C3}

type Two is Type:
  T{a: C3, b: Box}

def f(x: Two) -> C3:
  match x:
    case T{A{}, K{c}}:
      v = c
      v
    case T{_, _}: B{}

def main() -> C3:
  f(T{A{}, K{B{}}})
