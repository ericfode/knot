# The driver.bend checked and load shapes: a continuation next: Book -> Act(Color), captured by a bind lambda.
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

def checked(result: Res<Fault,Book>, next: Book -> Act(Color)) -> Act(Color):
  match result:
    case Fail{error}: Act.die(Color,error)
    case Done{book}: next(book)

def open(f: Flag) -> Act(Res<Fault,Book>):
  match f:
    case Off{}: Act.pure(Res<Fault,Book>,Fail{Invalid{}})
    case On{}: Act.pure(Res<Fault,Book>,Done{Book{On{}}})

def load(f: Flag, next: Book -> Act(Color)) -> Act(Color):
  Act.bind(Res<Fault,Book>,Color,open(f),result => checked(result,next))

def render(book: Book, g: Flag) -> Act(Color):
  match book:
    case Book{b}:
      match g:
        case Off{}: Act.pure(Color,Red{})
        case On{}: Act.pure(Color,Blue{})

def settle(o: Op<Color>) -> Color:
  match o:
    case Emit{c}: c
    case Halt{e}: Gray{}

def run(f: Flag, g: Flag) -> Color:
  settle(load(f,book => render(book,g),Color,c => Emit{c}))

def main() -> Color:
  run(On{},On{})
