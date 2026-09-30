type Light is Type:
  Dark{}
  Lit{}

def f(a.b: Light) -> Light:
  a.b : Light = a.b
  a.b

def main() -> Light:
  f(Lit{})
