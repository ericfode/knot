type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  copy : N = n
  match copy:
    case S{S{x}}: drain(x)
    case _: On{}
def main() -> Flag:
  drain(S{S{S{S{Z{}}}}})
