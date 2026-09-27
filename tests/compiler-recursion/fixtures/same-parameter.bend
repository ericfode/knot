type Peano is Data:
  Zero{}
  Succ{pred: Peano}
def f(n: Peano) -> Peano:
  f(n)
def main() -> Peano:
  f(Zero{})
