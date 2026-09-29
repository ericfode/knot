# A recursive call over two scrutinees whose first argument is not a part of the first parameter.
type Flag is Data:
  Off{}
  On{}

type N is Data:
  Z{}
  S{pred: N}

def swap(a: N, b: N) -> Flag:
  match a b:
    case Z{} _: On{}
    case S{x} y: swap(y, x)

def main() -> Flag:
  swap(S{Z{}}, S{Z{}})
