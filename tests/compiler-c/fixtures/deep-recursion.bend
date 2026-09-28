type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
def copy(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: Succ{copy(p)}
def parity(n: Peano, a: Flag, b: Flag) -> Flag:
  match n:
    case Zero{}: a
    case Succ{p}: parity(p,b,a)
def input() -> Peano:
  Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
def main() -> Flag:
  parity(copy(input()),Off{},On{})
