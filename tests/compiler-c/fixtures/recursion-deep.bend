type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano) -> Peano:
  match n:
    case Zero{}: Zero{}
    case Succ{p}: f(p)
def input() -> Peano:
  Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Succ{Zero{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
def main() -> Peano:
  f(input())

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
def c_observe() -> CObservation:
  c_literal_0(main())
