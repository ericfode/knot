type Light is Type:
  Dark{}
  Lit{}

def g(x: Light) -> Light:
  x

def f(y: Light) -> Light:
  match y:
    case Dark{}:
      Light : Light = Lit{}
      Light
    case Lit{}:
      z : Light = Dark{}
      g(z)

def main() -> Light:
  f(Lit{})
