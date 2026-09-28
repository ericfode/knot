type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def identity(n: N) -> N:
  n
def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}:
      next = identity(p)
      drain(next)
def main() -> Flag:
  drain(Z{})
