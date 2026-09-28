import Base

type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -h = Bool.not
  x

def main() -> Light:
  f(Lit{})
