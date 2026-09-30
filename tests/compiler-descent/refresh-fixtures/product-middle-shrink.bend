type Flag is Data:
  Off{}
  On{}
type N is Data:
  Z{}
  S{pred: N}
type Triple is Data:
  Triple{first: N, second: N, third: N}
def drain(t: Triple) -> Flag:
  match t:
    case Triple{a,Z{},c}: On{}
    case Triple{a,S{x},c}: drain(Triple{a,x,c})
def main() -> Flag:
  drain(Triple{S{Z{}},S{S{Z{}}},S{Z{}}})
