type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def identity(n: N) -> N:
  n
def drain(+a: N, n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{x}: drain(a,identity(x))
def main() -> Flag:
  drain(Z{},Z{})
