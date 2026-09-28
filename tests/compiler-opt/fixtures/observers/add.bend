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

type OptObservation is Data:
  OptMismatch{}
  OptMatch{}
def opt_and(a: OptObservation, b: OptObservation) -> OptObservation:
  match a:
    case OptMismatch{}: OptMismatch{}
    case OptMatch{}:
      match b:
        case OptMismatch{}: OptMismatch{}
        case OptMatch{}: OptMatch{}
def opt_check0(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMatch{}
    case Succ{p}: OptMismatch{}
def opt_check1(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check0(p)
def opt_check2(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check1(p)
def opt_check3(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check2(p)
def opt_check4(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check3(p)
def opt_check5(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check4(p)
def opt_exact(x: Results) -> OptObservation:
  match x:
    case Results{a,b,c,d}: opt_and(opt_check0(a),opt_and(opt_check3(b),opt_and(opt_check3(c),opt_check5(d))))
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Results{Zero{},Zero{},Zero{},Zero{}})
