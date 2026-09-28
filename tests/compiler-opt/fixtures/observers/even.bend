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
def opt_off(x: Flag) -> OptObservation:
  match x:
    case Off{}: OptMatch{}
    case On{}: OptMismatch{}
def opt_on(x: Flag) -> OptObservation:
  match x:
    case Off{}: OptMismatch{}
    case On{}: OptMatch{}
def opt_exact(x: Results) -> OptObservation:
  match x:
    case Results{a,b,c,d,e}: opt_and(opt_on(a),opt_and(opt_off(b),opt_and(opt_on(c),opt_and(opt_off(d),opt_on(e)))))
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Results{Off{},Off{},On{},Off{},On{}})
