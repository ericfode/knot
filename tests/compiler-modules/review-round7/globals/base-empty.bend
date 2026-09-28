import Base

type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -T = Empty
  x

def main() -> Light:
  f(Lit{})
