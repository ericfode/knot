type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -g = later
  x

def later(x: Light) -> Light:
  x

def main() -> Light:
  f(Lit{})
