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
        case W{b}:
          match b:
            case B{p}: both(p, p)
            case E{}: On{}

type Sel is Data:
  S0{}
  S1{}
  S2{}

def mkbox(s: Sel) -> Box:
  match s:
    case S0{}: B{Off{}}
    case S1{}: B{On{}}
    case S2{}: E{}

def mkwrap(s: Sel) -> Wrap:
  W{mkbox(s)}

def probe(s: Sel) -> Flag:
  f(mkwrap(s))
