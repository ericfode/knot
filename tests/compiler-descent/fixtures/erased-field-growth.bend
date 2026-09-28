type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type Pair is Data:
  Pair{-ghost: N, count: N}
def drain(pair: Pair) -> Flag:
  match pair:
    case Pair{_,Z{}}: On{}
    case Pair{ghost,S{b}}: drain(Pair{S{ghost},b})
def main() -> Flag:
  drain(Pair{Z{},Z{}})
