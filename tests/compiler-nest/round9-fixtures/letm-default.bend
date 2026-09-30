type C3 is Data:
  A{}
  B{}
  C{}

def f(y: C3, z: C3) -> C3:
  match y z:
    case A{} _: A{}
    case _ B{}:
      v = z
      v
    case _ _: C{}

def main() -> C3:
  f(B{}, B{})
