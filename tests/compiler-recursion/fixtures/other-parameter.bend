type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano, m: Peano) -> Peano:
  match m:
    case Zero{}: n
    case Succ{p}: f(p,Zero{})
def main() -> Peano:
  f(Zero{},Succ{Succ{Zero{}}})
