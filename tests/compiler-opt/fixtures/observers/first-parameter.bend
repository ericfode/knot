type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano, m: Peano) -> Peano:
  match n:
    case Zero{}: m
    case Succ{p}: f(p,Zero{})
def main() -> Peano:
  f(Succ{Succ{Zero{}}},Zero{})

type OptObservation is Data:
  OptMismatch{}
  OptMatch{}
def opt_check0(n: Peano) -> OptObservation:
  match n:
    case Zero{}: OptMatch{}
    case Succ{p}: OptMismatch{}
def opt_exact(x: Peano) -> OptObservation:
  opt_check0(x)
def opt_observe() -> OptObservation:
  opt_exact(main())
def opt_observe_bad() -> OptObservation:
  opt_exact(Succ{Zero{}})
