type Color is Data:
  Red{}
  Green{}
  Blue{}

def first(x: Color, y: Color) -> Color:
  match y:
    case Red{}: x
    case Green{}: x
    case Blue{}: x

def g(c: Color) -> Color:
  t = first(c, Red{})
  match t:
    case +u: first(u, Blue{})
