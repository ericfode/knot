# An erased type argument is passed to a live Type parameter at runtime.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def keep(A: Type, x: Flag) -> Flag:
  x

def pass(-A: Type, x: Flag) -> Flag:
  keep(A, x)

def main() -> Flag:
  pass(Color, On{})
