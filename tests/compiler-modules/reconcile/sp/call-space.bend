type Light is Type:
  Dark{}
  Lit{}

def g(x: Light) -> Light:
  x

def main() -> Light:
  g (Lit{})
