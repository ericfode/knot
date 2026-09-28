# The IO.bind(..,arguments) shape: a named def as a value, and one def named twice.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def then(-A: Type, -B: Type, x: A, next: A -> B) -> B:
  next(x)

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def pair(a: Color, b: Color) -> Color:
  match a:
    case Red{}: b
    case Blue{}: Blue{}

def each(k: Flag -> Color, j: Flag -> Color, f: Flag, g: Flag) -> Color:
  pair(k(f),j(g))

def one(f: Flag) -> Color:
  then(Flag,Color,f,paint)

def two(f: Flag, g: Flag) -> Color:
  each(paint,paint,f,g)

def main() -> Color:
  one(On{})
