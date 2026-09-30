type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(n: N) -> Flag:
  -discarded : Flag = drain(S{n})
  On{}
def main() -> Flag:
  drain(S{S{Z{}}})
