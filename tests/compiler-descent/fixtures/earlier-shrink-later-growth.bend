type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N, +m: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}: drain(p,S{m})
def main() -> Flag:
  drain(S{S{Z{}}},Z{})
