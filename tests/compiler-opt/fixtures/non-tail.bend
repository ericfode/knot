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
def parity(n: Peano) -> Flag:
  match n:
    case Zero{}: On{}
    case Succ{p}: flip(parity(p))
def main() -> Flag:
  parity(Succ{Succ{Succ{Zero{}}}})
