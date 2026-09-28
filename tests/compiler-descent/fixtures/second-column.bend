type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+fixed: N, n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}: drain(fixed,p)
def main() -> Flag:
  drain(S{Z{}},S{S{Z{}}})
