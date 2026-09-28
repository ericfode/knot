type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
  W{inner: N}
def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{p}: drain(p)
    case W{S{p}}: drain(S{p})
    case W{Z{}}: Off{}
    case W{W{p}}: drain(W{p})
def main() -> Flag:
  drain(W{S{W{S{Z{}}}}})
