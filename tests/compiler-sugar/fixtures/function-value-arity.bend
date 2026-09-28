# A two-parameter def is passed where a one-parameter function is expected.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def then(-A: Type, -B: Type, x: A, next: A -> B) -> B:
  next(x)

def shade(+base: Color, f: Flag) -> Color:
  match f:
    case Off{}: base
    case On{}: Blue{}

def run(f: Flag, c: Color) -> Color:
  then(Flag,Color,f,shade)

def main() -> Color:
  run(Off{},Red{})
