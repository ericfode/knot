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
      a = p
      b = a
      drain(b)
def main() -> Flag:
  drain(S{S{Z{}}})
