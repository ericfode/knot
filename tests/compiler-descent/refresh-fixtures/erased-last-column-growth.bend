type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N, -ghost: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{x}: drain(x,S{ghost})
def main() -> Flag:
  drain(S{S{Z{}}},Z{})
