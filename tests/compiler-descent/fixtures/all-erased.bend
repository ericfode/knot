type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
def drain(-ghost: N) -> Flag:
  drain(ghost)
def main() -> Flag:
  drain(Z{})
