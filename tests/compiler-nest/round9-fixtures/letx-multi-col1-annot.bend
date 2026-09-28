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

def f(z: C3, y: C3) -> C3:
  match z y:
    case A{} _:
      v : C3 = z
      v
    case _ _: B{}

def main() -> C3:
  A{}
