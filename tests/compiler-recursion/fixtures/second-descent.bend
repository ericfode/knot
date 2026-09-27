type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano, m: Peano) -> Peano:
  match m:
    case Zero{}: n
    case Succ{p}: f(n,p)
def main() -> Peano:
  f(Succ{Zero{}},Succ{Succ{Zero{}}})
