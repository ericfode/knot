type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: Flag, +b: N, n: N) -> Flag:
  match n:
    case Z{}: a
    case S{p}: drain(a,b,p)
def main() -> Flag:
  drain(On{},S{Z{}},S{S{Z{}}})
