# Named definitions applied to fewer arguments than parameters become closures.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def shift(c: Color) -> Color:
  match c:
    case Red{}: Green{}
    case Green{}: Blue{}
    case Blue{}: Red{}

def pick(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: invert(b)

def paint(a: Flag, b: Flag, c: Color) -> Color:
  match a:
    case Off{}:
      match b:
        case Off{}: c
        case On{}: shift(c)
    case On{}:
      match b:
        case Off{}: shift(shift(c))
        case On{}: Red{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def tint(f: Color -> Color, c: Color) -> Color:
  f(c)

def feed(f: Flag -> Color -> Color, b: Flag, c: Color) -> Color:
  f(b, c)

def one_of_two(a: Flag, x: Flag) -> Flag:
  apply(pick(a), x)

def two_of_three(a: Flag, b: Flag, c: Color) -> Color:
  tint(paint(a, b), c)

def one_of_three(a: Flag, b: Flag, c: Color) -> Color:
  feed(paint(a), b, c)

def main() -> Color:
  two_of_three(On{}, Off{}, Blue{})
