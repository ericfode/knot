type Flag is Data:
  Off{}
  On{}
type Peano is Type:
  Zero{}
  Succ{pred: Peano}
def add_one(x: Peano) -> Peano:
  Succ{x}
def is_one(x: Peano) -> Flag:
  match x:
    case Zero{}:
      Off{}
    case Succ{p}:
      match p:
        case Zero{}:
          On{}
        case Succ{q}:
          Off{}
def zero() -> Flag:
  is_one(Zero{})
def two() -> Flag:
  is_one(add_one(Succ{Zero{}}))
def main() -> Flag:
  is_one(add_one(Zero{}))
