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

def f(x: Box) -> Flag:
  match x:
    case +y:
      match y:
        case B{+p}: bx(B{p})
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
