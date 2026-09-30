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
    case T{A{}, K{b}}:
      v = x
      A{}
    case T{_, _}: C{}

def main() -> C3:
  A{}
