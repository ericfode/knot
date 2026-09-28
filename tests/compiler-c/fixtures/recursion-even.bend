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

type CObservation is Data:
  CNo{}
  CYes{}
def c_all(a: CObservation, b: CObservation) -> CObservation:
  match a:
    case CNo{}: CNo{}
    case CYes{}: b
def c_literal_0(value: Flag) -> CObservation:
  match value:
    case Off{}:
      CNo{}
    case On{}:
      CYes{}
def c_literal_1(value: Flag) -> CObservation:
  match value:
    case Off{}:
      CYes{}
    case On{}:
      CNo{}
def c_literal_2(value: Results) -> CObservation:
  match value:
    case Results{f0,f1,f2,f3,f4}:
      c_all(c_literal_0(f0),c_all(c_literal_1(f1),c_all(c_literal_0(f2),c_all(c_literal_1(f3),c_all(c_literal_0(f4),CYes{})))))
def c_observe() -> CObservation:
  c_literal_2(main())
