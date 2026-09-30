type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def identity(n: N) -> N:
  n
def drain(n: N, +later: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{x}: drain(x,identity(later))
def main() -> Flag:
  drain(S{S{Z{}}},Z{})
