type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano, m: Peano) -> Peano:
  match m:
    case Zero{}: n
    case Succ{p}: f(n,p)
def sample() -> Peano:
  f(Succ{Zero{}},Succ{Succ{Zero{}}})
type Flag is Data:
  Off{}
  On{}
def observe(n: Peano) -> Flag:
  match n:
    case Zero{}: Off{}
    case Succ{Zero{}}: On{}
    case Succ{Succ{p}}: Off{}
def main() -> Flag:
  observe(sample())
