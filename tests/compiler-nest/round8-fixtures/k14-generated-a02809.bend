type Flag is Data:
  Off{}
  On{}

type Box is Data:
  B{f: Flag}
  E{}

type Wrap is Type:
  W{b: Box, -g: Flag}

type Sel is Data:
  S0{}
  S1{}
  S2{}

def both(a: Flag, b: Flag) -> Flag:
  match a:
    case On{}: b
    case Off{}: Off{}

def keep(a: Flag, -b: Flag) -> Flag:
  a

def bkeep(a: Flag, -b: Box) -> Flag:
  a

def bx(x: Box) -> Flag:
  match x:
    case B{f}: f
    case E{}: On{}

def wx(w: Wrap) -> Flag:
  match w:
    case W{b, g}: bx(b)

def mkbox(s: Sel) -> Box:
  match s:
    case S0{}: B{Off{}}
    case S1{}: B{On{}}
    case S2{}: E{}

def mkwrap(s: Sel) -> Wrap:
  W{mkbox(s), On{}}

def mkflag(s: Sel) -> Flag:
  match s:
    case S0{}: Off{}
    case S1{}: On{}
    case S2{}: Off{}

def f(p0: Wrap, +p1: Box) -> Flag:
  match p0:
    case +v2:
      match v2:
        case W{_, +v3}: both(both(Off{}, On{}), both(Off{}, Off{}))
        case W{v4, _}: both(wx(v2), both(Off{}, On{}))

def probe(sp0: Sel, sp1: Sel) -> Flag:
  f(mkwrap(sp0), mkbox(sp1))
