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

def f(y: C3, z: C3) -> C3:
  match y z:
    case A{} B{}:
      +v = z
      v
    case _ _: B{}

def main() -> C3:
  A{}
