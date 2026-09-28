type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
type Chain is Type:
  End{}
  Link{head: Flag, tail: Chain}
type Results is Data:
  Results{empty: Peano, three: Peano}
def length(xs: Chain) -> Peano:
  match xs:
    case End{}: Zero{}
    case Link{head,tail}: Succ{length(tail)}
def main() -> Results:
  Results{length(End{}),length(Link{Off{},Link{On{},Link{Off{},End{}}}})}

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
def c_literal_4(value: Results) -> CObservation:
  match value:
    case Results{f0,f1}:
      c_all(c_literal_0(f0),c_all(c_literal_3(f1),CYes{}))
def c_observe() -> CObservation:
  c_literal_4(main())
