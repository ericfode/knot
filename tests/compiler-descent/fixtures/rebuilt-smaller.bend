type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case S{Z{}}: Off{}
    case S{S{p}}: drain(S{p})
def main() -> Flag:
  drain(S{S{S{Z{}}}})
