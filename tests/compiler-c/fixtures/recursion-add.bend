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

type CObservation is Data:
  CNo{}
  CYes{}
def c_all(a: CObservation, b: CObservation) -> CObservation:
  match a:
    case CNo{}: CNo{}
    case CYes{}: b
def c_literal_0(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CYes{}
    case Succ{f0}:
      CNo{}
def c_literal_1(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_0(f0),CYes{})
def c_literal_2(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_1(f0),CYes{})
def c_literal_3(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_2(f0),CYes{})
def c_literal_4(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_3(f0),CYes{})
def c_literal_5(value: Peano) -> CObservation:
  match value:
    case Zero{}:
      CNo{}
    case Succ{f0}:
      c_all(c_literal_4(f0),CYes{})
def c_literal_6(value: Results) -> CObservation:
  match value:
    case Results{f0,f1,f2,f3}:
      c_all(c_literal_0(f0),c_all(c_literal_3(f1),c_all(c_literal_3(f2),c_all(c_literal_5(f3),CYes{}))))
def c_observe() -> CObservation:
  c_literal_6(main())
