# A variable row aliases the rebuilt scrutinee, which is not smaller than the parameter.
type Flag is Data:
  Off{}
  On{}

type N is Data:
  Z{}
  S{pred: N}

def drain(n: N) -> Flag:
  match n:
    case Z{}: On{}
    case k: drain(k)

def main() -> Flag:
  drain(Z{})
