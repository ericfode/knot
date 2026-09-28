type Flag is Data:
  Off{}
  On{}
type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def copy(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: Succ{copy(p)}
def tag(n: Peano) -> Flag:
  match n:
    case Zero{}: Off{}
    case Succ{p}: On{}
def main() -> Flag:
  tag(copy(Succ{Zero{}}))
