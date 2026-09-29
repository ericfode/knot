type C3 is Data:
  A{}
  B{}

type Box is Type:
  K{c: C3}

def g(x: Box) -> C3:
  match x:
    case K{c}: c

def f(x: Box) -> C3:
  match x:
    case K{A{}}:
      v = x
      g(v)
    case K{_}: B{}

def main() -> C3:
  f(K{A{}})
