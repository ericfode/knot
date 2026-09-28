# Pack{On{},Red{}}: when fst is On, snd must be Shade(On) = Flag.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b):
  Pack{fst: A, snd: B(fst)}

def Shade(f: Flag) -> Data:
  match f:
    case Off{}: Color
    case On{}: Flag

def tone(c: Color) -> Flag:
  match c:
    case Red{}: Off{}
    case Blue{}: On{}

def read(p: Dep<&2,&2,Flag,x => Shade(x)>) -> Flag:
  match p:
    case Pack{Off{},c}: tone(c)
    case Pack{On{},g}: g

def made(f: Flag, g: Flag) -> Dep<&2,&2,Flag,x => Shade(x)>:
  match f:
    case Off{}:
      match g:
        case Off{}: Pack{Off{},Red{}}
        case On{}: Pack{Off{},Blue{}}
    case On{}: Pack{On{},Red{}}

def round(f: Flag, g: Flag) -> Flag:
  read(made(f,g))

def main() -> Flag:
  round(Off{},On{})
