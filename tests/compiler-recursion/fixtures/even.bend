type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
type Results is Data:
  Results{zero: Flag, one: Flag, two: Flag, five: Flag, six: Flag}
def even(n: Peano) -> Flag:
  match n:
    case Zero{}: On{}
    case Succ{p}:
      match p:
        case Zero{}: Off{}
        case Succ{q}: even(q)
def main() -> Results:
  Results{even(Zero{}),even(Succ{Zero{}}),even(Succ{Succ{Zero{}}}),even(Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}),even(Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}})}
