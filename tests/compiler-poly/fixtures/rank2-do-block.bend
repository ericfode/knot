# The driver.bend read_pair do block over the rank-2 monad: do Act<Color> desugars to Act.bind and Act.pure.
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

def paint(f: Flag) -> Act(Color):
  match f:
    case Off{}: Act.die(Color,Unsupported{})
    case On{}: Act.pure(Color,Blue{})

def mix(c: Color, g: Flag) -> Color:
  match g:
    case Off{}: c
    case On{}: Red{}

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def steps(f: Flag, g: Flag) -> Act(Color):
  do Act<Color>:
    x : Flag <- Act.pure(Flag,f)
    c : Color <- paint(x)
    return mix(c,g)

def run(f: Flag, g: Flag) -> Color:
  settle(steps(f,g,Color,c => Emit{c}))

def main() -> Color:
  run(On{},Off{})
