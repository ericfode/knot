type C3 is Data:
  A{}
  B{}

def f(z: C3) -> C3:
  match z:
    case A{}:
      v = z
      v
    case B{}: B{}

def main() -> C3:
  f(A{})
