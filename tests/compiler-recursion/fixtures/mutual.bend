type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano) -> Peano:
  g(n)
def g(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: f(p)
def main() -> Peano:
  f(Succ{Succ{Zero{}}})
