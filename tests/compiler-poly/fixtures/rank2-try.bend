# The IO.pass and IO.try shapes: Act.bind at Res<Fault,A> under a rigid A, fed Act.pass(A), a generic def applied to its type argument alone.
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

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

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

def Act.pass(-A: Type, r: Res<Fault,A>) -> Act(A):
  match r:
    case Fail{e}: Act.die(A,e)
    case Done{x}: Act.pure(A,x)

def Act.try(-A: Type, act: Act(Res<Fault,A>)) -> Act(A):
  Act.bind(Res<Fault,A>,A,act,Act.pass(A))

def lookup(f: Flag, g: Flag) -> Act(Res<Fault,Color>):
  match f:
    case Off{}:
      match g:
        case Off{}: Act.pure(Res<Fault,Color>,Fail{Invalid{}})
        case On{}: Act.pure(Res<Fault,Color>,Fail{Unsupported{}})
    case On{}: Act.pure(Res<Fault,Color>,Done{Blue{}})

def outcome(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{Invalid{}}: Red{}
    case Halt{Unsupported{}}: Gray{}

def run(f: Flag, g: Flag) -> Color:
  outcome(Act.try(Color,lookup(f,g),Color,c => Emit{c}))

def main() -> Color:
  run(Off{},On{})
