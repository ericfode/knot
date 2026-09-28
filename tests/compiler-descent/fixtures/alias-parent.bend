type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}:
      next : N = n
      drain(next)
def main() -> Flag:
  drain(Z{})
