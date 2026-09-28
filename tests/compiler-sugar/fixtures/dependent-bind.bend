# The S.bind shape: -A: Data and -B: Data thread a result through a continuation.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Outcome<-A: Data> is Data:
  Failed{code: Flag}
  Passed{value: A}

def bind(-A: Data, -B: Data, result: Outcome<A>, next: A -> Outcome<B>) -> Outcome<B>:
  match result:
    case Failed{e}: Failed{e}
    case Passed{x}: next(x)

def paint(f: Flag) -> Outcome<Color>:
  match f:
    case Off{}: Failed{On{}}
    case On{}: Passed{Blue{}}

def settle(o: Outcome<Color>) -> Color:
  match o:
    case Failed{e}: Red{}
    case Passed{c}: c

def start(f: Flag, g: Flag) -> Outcome<Flag>:
  match f:
    case Off{}: Failed{g}
    case On{}: Passed{g}

def run(f: Flag, g: Flag) -> Color:
  settle(bind(Flag,Color,start(f,g),x => paint(x)))

def main() -> Color:
  run(On{},On{})
