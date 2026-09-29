# A U32 result displays as the seed's decimal literal.
import Base

type Sample is Type:
  Least{}
  Hundreds{}
  Most{}
  Wrapped{}
  Shifted{}

def sample(s: Sample) -> U32:
  match s:
    case Least{}: 0
    case Hundreds{}: 300
    case Most{}: 4294967295
    case Wrapped{}: U32.sub(0, 1)
    case Shifted{}: U32.shln(1, 31n)

def main() -> U32:
  sample(Hundreds{})
