# Negative twin of erased-value-arg: an erased argument is still type-checked.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def ghost(-A: Type, -w: A, x: Flag) -> Flag:
  x

def main() -> Flag:
  ghost(Color, On{}, On{})
