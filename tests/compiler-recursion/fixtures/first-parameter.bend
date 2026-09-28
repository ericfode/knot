type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano, m: Peano) -> Peano:
  match n:
    case Zero{}: m
    case Succ{p}: f(p,Zero{})
def main() -> Peano:
  f(Succ{Succ{Zero{}}},Zero{})
