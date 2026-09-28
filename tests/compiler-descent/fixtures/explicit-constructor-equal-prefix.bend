type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, n: N) -> Flag:
  match a n:
    case Z{} _: Off{}
    case S{x} Z{}: On{}
    case S{x} S{p}: drain(S{x},p)
def main() -> Flag:
  drain(S{Z{}},S{S{Z{}}})
