type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  match n:
    case S{S{S{x}}}: drain(S{S{x}})
    case _: On{}
def main() -> Flag:
  drain(S{S{S{S{S{Z{}}}}}})
