type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+a: N, -ghost: N, +b: N) -> Flag:
  match ghost:
    case Z{}: On{}
    case S{x}: drain(a,x,b)
def main() -> Flag:
  drain(Z{},Z{},Z{})
