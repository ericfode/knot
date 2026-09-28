type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def g(n: Peano) -> Peano:
  n
def f(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: f(g(p))
def main() -> Peano:
  f(Succ{Succ{Zero{}}})
