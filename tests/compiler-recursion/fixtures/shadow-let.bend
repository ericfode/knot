type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}:
      p : Peano = Succ{p}
      f(p)
def main() -> Peano:
  f(Succ{Zero{}})
