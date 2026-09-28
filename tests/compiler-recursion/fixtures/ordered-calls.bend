type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def g(n: Peano) -> Peano:
  n
def f(n: Peano) -> Peano:
  g(n)
def main() -> Peano:
  f(Succ{Zero{}})
