type C3 is Data:
  A{}
  B{}

type Box is Type:
  K{c: C3}

def f(x: Box) -> C3:
  match x:
    case K{c}:
      v = c
      v

def main() -> C3:
  f(K{A{}})
