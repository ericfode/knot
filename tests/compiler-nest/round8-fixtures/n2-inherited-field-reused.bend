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

type Wrap is Type:
  W{b: Box}

def f(w: Wrap) -> Flag:
  match w:
    case +y:
      match y:
        case W{b}: both(bx(b), bx(b))
