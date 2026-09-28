# The driver.bend read_pair do block, statement-only: do Act<Color> runs close(f), then paint(g), desugared to Act.bind.
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

type Unit is Data:
  Unit{}

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

def close(f: Flag) -> Act(Unit):
  match f:
    case Off{}: Act.die(Unit,Invalid{})
    case On{}: Act.pure(Unit,Unit{})

def paint(g: Flag) -> Act(Color):
  match g:
    case Off{}: Act.pure(Color,Red{})
    case On{}: Act.pure(Color,Blue{})

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def steps(f: Flag, g: Flag) -> Act(Color):
  do Act<Color>:
    close(f)
    paint(g)

def run(f: Flag, g: Flag) -> Color:
  settle(steps(f,g,Color,c => Emit{c}))

def main() -> Color:
  run(On{},Off{})
