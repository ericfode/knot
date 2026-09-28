# S.bind called from generic code: then forwards its own A, B, C and captures f and g at rigid arrows.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def bind(-A: Data, -B: Data, result: Res<Fault,A>, next: A -> Res<Fault,B>) -> Res<Fault,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def then(-A: Data, -B: Data, -C: Data, r: Res<Fault,A>, f: A -> Res<Fault,B>, g: B -> Res<Fault,C>) -> Res<Fault,C>:
  bind(A,C,r,x => bind(B,C,f(x),g))

def start(f: Flag) -> Res<Fault,Flag>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{On{}}

def paint(f: Flag) -> Res<Fault,Color>:
  match f:
    case Off{}: Fail{Unsupported{}}
    case On{}: Done{Blue{}}

def tone(c: Color) -> Res<Fault,Flag>:
  match c:
    case Red{}: Fail{Unsupported{}}
    case Blue{}: Done{Off{}}

def gate(g: Flag, f: Flag) -> Res<Fault,Flag>:
  match g:
    case Off{}: Done{f}
    case On{}: Fail{Unsupported{}}

def fault(-A: Data, r: Res<Fault,A>) -> Fault:
  match r:
    case Fail{e}: e
    case Done{x}: Invalid{}

def flag_of(r: Res<Fault,Flag>) -> Flag:
  match r:
    case Fail{e}: On{}
    case Done{x}: x

def colors(f: Flag) -> Flag:
  flag_of(then(Flag,Color,Flag,start(f),paint,tone))

def flags(f: Flag, g: Flag) -> Fault:
  fault(Color,then(Flag,Flag,Color,start(f),x => gate(g,x),paint))

def main() -> Flag:
  colors(On{})
