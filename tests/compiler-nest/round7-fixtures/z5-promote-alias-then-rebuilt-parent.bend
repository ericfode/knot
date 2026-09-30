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

def g(b: Box) -> Flag:
  match b:
    case B{v}: v
    case E{}: On{}

def f(x: Box) -> Flag:
  match x:
    case B{On{}}: Off{}
    case +y: both(g(y), g(x))
