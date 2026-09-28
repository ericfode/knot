# A Color -> Color definition is passed where Flag -> Flag is expected.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def shade(c: Color) -> Color:
  c

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def main() -> Flag:
  apply(shade, On{})
