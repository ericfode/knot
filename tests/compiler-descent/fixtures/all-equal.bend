type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(+n: N, +m: N) -> Flag:
  drain(n,m)
def main() -> Flag:
  drain(Z{},Z{})
