type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
def swap_tail(n: Peano, a: Flag, b: Flag) -> Flag:
  match n:
    case Zero{}: a
    case Succ{p}: swap_tail(p,b,a)
def odd(a: Flag, b: Flag) -> Flag:
  swap_tail(Succ{Zero{}},a,b)
def even(a: Flag, b: Flag) -> Flag:
  swap_tail(Succ{Succ{Zero{}}},a,b)
def main() -> Flag:
  odd(Off{},On{})
