# A curried continuation Flag -> Flag -> Color -> Color, fed x => y => z => and applied spread or stepwise.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def shift(c: Color) -> Color:
  match c:
    case Red{}: Green{}
    case Green{}: Blue{}
    case Blue{}: Red{}

def mix(a: Flag, b: Flag, c: Color) -> Color:
  match a:
    case Off{}:
      match b:
        case Off{}: c
        case On{}: shift(c)
    case On{}:
      match b:
        case Off{}: shift(shift(c))
        case On{}: Red{}

def spread(a: Flag, b: Flag, c: Color, next: Flag -> Flag -> Color -> Color) -> Color:
  next(a, b, c)

def stepwise(a: Flag, b: Flag, c: Color, next: Flag -> Flag -> Color -> Color) -> Color:
  next(a)(b)(c)

def run_spread(a: Flag, b: Flag, c: Color) -> Color:
  spread(a, b, c, x => y => z => mix(x, y, z))

def run_stepwise(a: Flag, b: Flag, c: Color) -> Color:
  stepwise(a, b, c, x => y => z => mix(y, x, z))

def main() -> Color:
  run_spread(Off{}, On{}, Red{})
