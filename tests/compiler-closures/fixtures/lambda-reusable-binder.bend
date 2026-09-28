# A + lambda binder over a Data type is used twice, as in S.bind(..., +reference => ...); a plain binder at a function type is applied once.
type Flag is Data:
  Off{}
  On{}

type Pair is Data:
  Pair{a: Flag, b: Flag}

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def make(f: Flag -> Pair, x: Flag) -> Pair:
  f(x)

def left(p: Pair) -> Flag:
  match p:
    case Pair{a, b}: a

def right(p: Pair) -> Flag:
  match p:
    case Pair{a, b}: b

def lift(h: (Flag -> Flag) -> Flag) -> Flag:
  h(invert)

def run_left(x: Flag) -> Flag:
  left(make(+y => Pair{y, invert(y)}, x))

def run_right(x: Flag) -> Flag:
  right(make(+y => Pair{y, invert(y)}, x))

def run_lift(x: Flag) -> Flag:
  lift(g => g(x))

def main() -> Flag:
  run_right(On{})
