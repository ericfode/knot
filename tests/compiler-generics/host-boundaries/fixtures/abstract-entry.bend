type Color is Data:
  Red{}
  Green{}

type Flag is Data:
  Off{}
  On{}

def identity(-A: Type, x: A) -> A:
  x

def round(x: Flag) -> Flag:
  identity(Flag, x)

def main() -> Flag:
  round(On{})
