type C3 is Data:
  A{}
  B{}

def f(y: C3, z: C3) -> C3:
  match y z:
    case A{} A{}:
      v : C3 = z
      v
    case _ _: B{}

def main() -> C3:
  f(A{}, A{})
