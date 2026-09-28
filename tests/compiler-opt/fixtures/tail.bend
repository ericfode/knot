type Flag is Data:
  Off{}
  On{}
type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def last(n: Peano, x: Flag) -> Flag:
  match n:
    case Zero{}: x
    case Succ{p}: last(p,x)
def main() -> Flag:
  last(Succ{Succ{Succ{Zero{}}}},On{})
