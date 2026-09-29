type Flag is Data:
  Off{}
  On{}

type Box is Type:
  B{f: Flag}
  E{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def bx(x: Box) -> Flag:
  match x:
    case B{f}: f
    case E{}: On{}

def f(x: Box, w: Box) -> Flag:
  match x w:
    case +y B{q}: q
    case +y E{}: On{}
