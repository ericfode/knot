type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{x}:
      n : N = x
      drain(n)
def main() -> Flag:
  drain(S{S{Z{}}})
