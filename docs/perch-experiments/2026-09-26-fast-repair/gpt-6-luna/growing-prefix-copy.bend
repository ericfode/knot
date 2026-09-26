import Base

def map_values(xs: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.add(U32.mul(h, 3), 1) <> map_values(t)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  map_values(xs)
