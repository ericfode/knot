type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -a.b = x
  x

def main() -> Light:
  f(Lit{})
