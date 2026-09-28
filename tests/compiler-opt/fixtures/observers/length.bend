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
def opt_exact(x: Results) -> OptObservation:
  match x:
    case Results{a,b}: opt_and(opt_check0(a),opt_check3(b))
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Results{Zero{},Zero{}})
