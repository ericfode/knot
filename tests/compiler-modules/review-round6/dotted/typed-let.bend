type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  a.b : Light = x
  a.b

def main() -> Light:
  f(Lit{})
