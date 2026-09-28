type Light is Type:
  Dark{}
  Lit{}

def konst(x: Light) -> Light -> Light:
  y => x

def main() -> Light:
  konst(Lit{})(Dark{})
