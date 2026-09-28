type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def g(n: Peano) -> Peano:
  n
def f(n: Peano) -> Peano:
  g(n)
def main() -> Peano:
  f(Succ{Zero{}})

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
def c_observe() -> CObservation:
  c_literal_1(main())
