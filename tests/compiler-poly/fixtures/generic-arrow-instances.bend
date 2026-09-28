# Type variables instantiated at arrows: apply's A is Flag -> Res<Fault,Flag>, and its B a Res instance.
type Flag is Data:
  Off{}
  On{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def apply(-A: Type, -B: Type, f: A -> B, x: A) -> B:
  f(x)

def guard(f: Flag) -> Res<Fault,Flag>:
  match f:
    case Off{}: Fail{Invalid{}}
    case On{}: Done{Off{}}

def lift(x: Flag) -> Res<Fault,Flag>:
  Done{x}

def outcome(r: Res<Fault,Flag>) -> Flag:
  match r:
    case Fail{e}: On{}
    case Done{x}: x

def guard_or_lift(c: Flag) -> Flag -> Res<Fault,Flag>:
  match c:
    case Off{}: guard
    case On{}: lift

def feed(x: Flag, c: Flag) -> Flag:
  outcome(apply(Flag -> Res<Fault,Flag>,Res<Fault,Flag>,h => h(x),guard_or_lift(c)))

def main() -> Flag:
  feed(Off{},Off{})
