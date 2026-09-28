# A parallel let binds two names to two calls.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def run(f: Flag, g: Flag) -> Color:
  a b = paint(f) paint(g)
  b

def main() -> Color:
  run(Off{},On{})
