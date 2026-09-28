# The Base IO(A) shape on fixture types: Act(A) = @-R: Type -> (A -> Op<R>) -> Op<R>, with pure, bind, die and a run.
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

def mix(c: Color, g: Flag) -> Act(Color):
  match g:
    case Off{}: Act.pure(Color,c)
    case On{}: Act.pure(Color,Red{})

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def run(m: Act(Color)) -> Color:
  settle(m(Color,c => Emit{c}))

def chain(f: Flag, g: Flag) -> Color:
  run(Act.bind(Color,Color,paint(f),c => mix(c,g)))

def nested(f: Flag, g: Flag) -> Color:
  run(Act.bind(Flag,Color,Act.pure(Flag,f),x =>
    Act.bind(Color,Color,paint(x),c =>
      mix(c,g))))

def main() -> Color:
  chain(On{},Off{})
