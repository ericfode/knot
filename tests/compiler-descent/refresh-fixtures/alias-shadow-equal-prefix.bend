type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{x}:
      a : N = a
      drain(a,x)
def main() -> Flag:
  drain(S{Z{}},S{S{Z{}}})
