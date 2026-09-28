type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def g(n: Peano) -> Peano:
  n
def f(n: Peano) -> Peano:
  g(n)
def main() -> Peano:
  f(Succ{Zero{}})

type OptObservation is Data:
  OptMismatch{}
  OptMatch{}
def opt_check0(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMatch{}
    case Succ{p}: OptMismatch{}
def opt_check1(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMismatch{}
    case Succ{p}: opt_check0(p)
def opt_exact(x: Peano) -> OptObservation:
  opt_check1(x)
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Zero{})
