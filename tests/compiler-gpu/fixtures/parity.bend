type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
def even(n: Peano) -> Flag:
  match n:
    case Zero{}: On{}
    case Succ{p}:
      match p:
        case Zero{}: Off{}
        case Succ{q}: even(q)
def zero() -> Flag:
  even(Zero{})
def one() -> Flag:
  even(Succ{Zero{}})
def two() -> Flag:
  even(Succ{Succ{Zero{}}})
def five() -> Flag:
  even(Succ{Succ{Succ{Succ{Succ{Zero{}}}}}})
def six() -> Flag:
  even(Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}})
def main() -> Flag:
  five()
