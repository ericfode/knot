# One Act(Flag) value run at two answer types: the action itself is affine.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}
  Gray{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Op<-R: Type> is Type:
  Emit{value: R}
  Halt{code: Fault}

def Act(-A: Type) -> Type:
  @-R: Type ->
  @k: (A -> Op<R>) ->
  Op<R>

def Act.pure(-A: Type, x: A) -> Act(A):
  R => k => k(x)

def Act.bind(-A: Type, -B: Type, m: Act(A), f: A -> Act(B)) -> Act(B):
  R => k => m(R,x => f(x,R,k))

def Act.die(-A: Type, code: Fault) -> Act(A):
  R => k => Halt{code}

def Act.join(-A: Type, mm: Act(Act(A))) -> Act(A):
  Act.bind(Act(A),A,mm,m => m)

def probe(f: Flag) -> Act(Flag):
  match f:
    case Off{}: Act.die(Flag,Invalid{})
    case On{}: Act.pure(Flag,Off{})

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def colored(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def flagged(o: Op<Flag>) -> Flag:
  match o:
    case Emit{x}: x
    case Halt{e}: On{}

def as_color(f: Flag) -> Color:
  colored(probe(f,Color,x => Emit{paint(x)}))

def as_flag(f: Flag) -> Flag:
  flagged(probe(f,Flag,x => Emit{x}))

def joined(f: Flag) -> Color:
  colored(Act.join(Flag,Act.pure(Act(Flag),probe(f)),Color,x => Emit{paint(x)}))

def both(m: Act(Flag)) -> Color:
  colored(m(Color,x => Emit{paint(flagged(m(Flag,y => Emit{y})))}))

def twice(f: Flag) -> Color:
  both(probe(f))

def main() -> Color:
  joined(On{})
