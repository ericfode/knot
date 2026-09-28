type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -T = Light
  x

def main() -> Light:
  f(Lit{})
