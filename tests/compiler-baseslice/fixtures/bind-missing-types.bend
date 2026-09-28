import Base

type Step is Data:
  Ready{}
  Stopped{}
  Failed{}

type Light is Data:
  Dark{}
  Lit{}

type Outcome is Data:
  BothLit{}
  SomeDark{}
  Halted5{}
  Halted2{}
  HaltedOther{}

# IO(A) is a continuation-passing function, so a pure run supplies Emit as the
# continuation and reads the resulting IO.OP.
def emit(-A: Type, x: A) -> IO(A):
  R => k => k(x)

def halted(five: Bool, two: Bool) -> Outcome:
  match five two:
    case True{} _: Halted5{}
    case False{} True{}: Halted2{}
    case False{} False{}: HaltedOther{}

def outcome(op: IO.OP<Outcome>) -> Outcome:
  match op:
    case Emit{v}: v
    case Halt{+code, message}: halted(Bool.and(U32.is_eq(code, 5), String.eq(message, "HostFailure")), U32.is_eq(code, 2))

def run(m: IO(Outcome)) -> Outcome:
  outcome(m(Outcome, x => Emit{x}))

def start(s: Step) -> IO(Light):
  match s:
    case Ready{}: emit(Light, Lit{})
    case Stopped{}: IO.die(Light, 5, "HostFailure")
    case Failed{}: IO.die(Light, 2, "Invalid")

def both(x: Light, y: Light) -> Outcome:
  match x y:
    case Lit{} Lit{}: BothLit{}
    case _ _: SomeDark{}

# The driver's shape: IO.bind(A, B, effect, value => next).
def drive(s: Step) -> Outcome:
  run(IO.bind(start(s), x => emit(Outcome, both(x, Lit{}))))

# The first IO.die wins: the second step never runs after a halt.
def twice(a: Step, b: Step) -> Outcome:
  run(IO.bind(Light, Outcome, start(a), x =>
    IO.bind(Light, Outcome, start(b), y => emit(Outcome, both(x, y)))))

def main() -> Outcome:
  twice(Failed{}, Stopped{})
