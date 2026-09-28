type Flag is Data:
  Off{}
  On{}
type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}
def walk(n: Peano, acc: Flag) -> Flag:
  match n:
    case Zero{}: acc
    case Succ{p}:
      next = flip(acc)
      walk(p,next)
def main() -> Flag:
  walk(Succ{Zero{}},Off{})
