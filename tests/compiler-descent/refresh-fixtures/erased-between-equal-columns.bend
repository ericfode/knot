type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, -ghost: N, +b: N, c: N) -> Flag:
  match c:
    case Z{}: On{}
    case S{x}: drain(a,S{ghost},b,x)
def main() -> Flag:
  drain(Z{},Z{},Z{},S{S{Z{}}})
