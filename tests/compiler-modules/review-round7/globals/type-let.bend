type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  T = Light
  y : T = Lit{}
  y

def main() -> Light:
  f(Lit{})
