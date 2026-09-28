type Flag is Data:
  Off{}
  On{}

type Box is Data:
  B{f: Flag}
  E{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def f(x: Box) -> Flag:
  match x:
    case B{g}:
      k = g
      match k:
        case +y: both(y, y)
    case E{}: Off{}
