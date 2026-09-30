type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, n: N) -> Flag:
  copy : N = a
  match a n:
    case Z{} _: On{}
    case S{x} Z{}: On{}
    case S{x} S{y}: drain(copy,y)
def main() -> Flag:
  drain(S{Z{}},S{S{Z{}}})
