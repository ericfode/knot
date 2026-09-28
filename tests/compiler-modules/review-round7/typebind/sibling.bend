type Light is Type:
  Dark{}
  Lit{}

type Flag is Type:
  Off{}
  On{}

def f(Light: Light) -> Flag:
  On{}

def g(x: Light) -> Light:
  x

def main() -> Light:
  g(Lit{})
