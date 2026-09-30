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
    case Triple{Z{},b,c}: On{}
    case Triple{S{x},b,c}:
      copy : Triple = Triple{S{x},b,c}
      drain(copy)
def main() -> Flag:
  drain(Triple{Z{},Z{},Z{}})
