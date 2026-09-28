# The check-cli.bend open_source shape: a partial application, then a named def, as the f of a rank-2 bind.
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

type Book is Data:
  Book{flag: Flag}

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

def open(f: Flag) -> Act(Res<Fault,Book>):
  match f:
    case Off{}: Act.pure(Res<Fault,Book>,Fail{Unsupported{}})
    case On{}: Act.pure(Res<Fault,Book>,Done{Book{Off{}}})

def paint(f: Flag) -> Act(Color):
  match f:
    case Off{}: Act.pure(Color,Red{})
    case On{}: Act.pure(Color,Blue{})

def opened(depth: Flag, result: Res<Fault,Book>) -> Act(Color):
  match result:
    case Fail{e}: Act.die(Color,e)
    case Done{book}:
      match book:
        case Book{b}: paint(depth)

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def run(m: Act(Color)) -> Color:
  settle(m(Color,c => Emit{c}))

def open_source(f: Flag, depth: Flag) -> Color:
  run(Act.bind(Res<Fault,Book>,Color,open(f),opened(depth)))

def arguments(f: Flag) -> Color:
  run(Act.bind(Flag,Color,Act.pure(Flag,f),paint))

def main() -> Color:
  open_source(On{},On{})
