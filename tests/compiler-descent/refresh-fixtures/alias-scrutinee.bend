type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  copy : N = n
  match copy:
    case Z{}: On{}
    case S{x}: drain(x)
def main() -> Flag:
  drain(S{S{Z{}}})
