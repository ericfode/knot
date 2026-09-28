type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -g = Lit
  x

def main() -> Light:
  f(Lit{})
