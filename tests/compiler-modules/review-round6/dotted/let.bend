type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  a.b = x
  a.b

def main() -> Light:
  f(Lit{})
