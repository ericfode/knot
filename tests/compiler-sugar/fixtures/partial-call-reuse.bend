# A let-bound partial application is used twice.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def each(k: Flag -> Color, j: Flag -> Color, f: Flag) -> Color:
  k(f)

def shade(+base: Color, f: Flag) -> Color:
  match f:
    case Off{}: base
    case On{}: Blue{}

def run(f: Flag, c: Color) -> Color:
  k = shade(c)
  each(k,k,f)

def main() -> Color:
  run(Off{},Red{})
