type C3 is Data:
  A{}
  B{}

def g(z: C3) -> C3:
  z

def f(y: C3, z: C3) -> C3:
  match y z:
    case A{} A{}:
      v = g(z)
      v
    case _ _: B{}

def main() -> C3:
  f(A{}, A{})
