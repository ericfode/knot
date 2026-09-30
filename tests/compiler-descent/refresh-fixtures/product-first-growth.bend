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
    case Triple{a,b,Z{}}: On{}
    case Triple{a,b,S{x}}: drain(Triple{S{a},b,x})
def main() -> Flag:
  drain(Triple{Z{},Z{},Z{}})
