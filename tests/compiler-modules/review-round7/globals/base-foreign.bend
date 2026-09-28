import Base

type Light is Type:
  Dark{}
  Lit{}

def f(x: Light) -> Light:
  -h = IO.write
  x

def main() -> Light:
  f(Lit{})
