type Flag is Data:
  Off{}
  On{}

type Box is Type:
  B{f: Flag}
  E{}

type Wrap is Type:
  W{b: Box, c: Box}

def bx(x: Box) -> Flag:
  match x:
    case B{f}: f
    case E{}: On{}

def f(w: Wrap) -> Flag:
  match w:
    case W{+b, c}: bx(b)
