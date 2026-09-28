type Light is Type:
  Dark{}
  Lit{}

def f(-Light: Type, x: Light) -> Light:
  x

def main() -> Light:
  f(Light, Lit{})
