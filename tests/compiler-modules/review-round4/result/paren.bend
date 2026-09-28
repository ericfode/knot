type Light is Type:
  Dark{}
  Lit{}

def keep(x: Light) -> (Light):
  x

def main() -> Light:
  keep(Lit{})
