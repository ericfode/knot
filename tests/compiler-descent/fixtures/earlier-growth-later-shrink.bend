type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+n: N, m: N) -> Flag:
  match m:
    case Z{}: On{}
    case S{p}: drain(S{n},p)
def main() -> Flag:
  drain(Z{},S{Z{}})
