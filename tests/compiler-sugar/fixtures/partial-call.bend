# The IO.bind(..,read_pair(characters,depth)) shape: a def given fewer arguments, passed on.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def then(-A: Type, -B: Type, x: A, next: A -> B) -> B:
  next(x)

def both(-A: Type, x: A, y: A, k: A -> A -> Color) -> Color:
  k(x,y)

def shade(+base: Color, f: Flag) -> Color:
  match f:
    case Off{}: base
    case On{}: Blue{}

def blend(+base: Color, f: Flag, g: Flag) -> Color:
  match f:
    case Off{}: base
    case On{}: shade(base,g)

def one(f: Flag, c: Color) -> Color:
  then(Flag,Color,f,shade(c))

def two(f: Flag, g: Flag, c: Color) -> Color:
  both(Flag,f,g,blend(c))

def main() -> Color:
  one(Off{},Red{})
