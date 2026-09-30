type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def f(m: N) -> Flag:
  match m:
    case Z{}: On{}
    case k:
      match k:
        case S{x}: f(x)
def main() -> Flag:
  f(S{S{Z{}}})
