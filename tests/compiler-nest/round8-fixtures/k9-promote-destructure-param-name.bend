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

def f(x: Box) -> Flag:
  match x:
    case +y:
      match x:
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

def probe(s: Sel) -> Flag:
  f(mkbox(s))
