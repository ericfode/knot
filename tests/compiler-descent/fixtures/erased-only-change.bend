type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(-ghost: N, +n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}: drain(p,n)
def main() -> Flag:
  drain(Z{},Z{})
