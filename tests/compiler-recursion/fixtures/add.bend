type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Results is Data:
  Results{zero: Peano, left: Peano, right: Peano, both: Peano}
def add(n: Peano, m: Peano) -> Peano:
  match n:
    case Zero{}: m
    case Succ{p}: Succ{add(p,m)}
def main() -> Results:
  Results{add(Zero{},Zero{}),add(Zero{},Succ{Succ{Succ{Zero{}}}}),add(Succ{Succ{Succ{Zero{}}}},Zero{}),add(Succ{Succ{Zero{}}},Succ{Succ{Succ{Zero{}}}})}
