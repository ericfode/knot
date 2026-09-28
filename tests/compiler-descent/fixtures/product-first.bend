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
    case Pair{Z{},_}: On{}
    case Pair{S{a},b}: drain(Pair{a,b})
def main() -> Flag:
  drain(Pair{S{S{Z{}}},S{Z{}}})
