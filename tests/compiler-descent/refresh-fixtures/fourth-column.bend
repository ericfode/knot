type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, +b: N, +c: N, d: N) -> Flag:
  match d:
    case Z{}: On{}
    case S{x}: drain(a,b,c,x)
def main() -> Flag:
  drain(Z{},S{Z{}},S{S{Z{}}},S{S{S{Z{}}}})
