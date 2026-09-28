type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type Pair is Data:
  Pair{left: N, right: N}
def drain(pair: Pair) -> Flag:
  match pair:
    case Pair{_,Z{}}: On{}
    case Pair{a,S{b}}: drain(Pair{a,b})
def main() -> Flag:
  drain(Pair{S{Z{}},S{S{Z{}}}})
