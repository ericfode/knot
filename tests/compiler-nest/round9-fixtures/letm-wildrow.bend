type C3 is Data:
  A{}
  B{}

def f(y: C3, z: C3) -> C3:
  match y z:
    case A{} _: A{}
    case _ _:
      v = y
      v

def main() -> C3:
  f(B{}, B{})
