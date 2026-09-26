import Base

def each(~f: U32 -> U32, xs: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t: f(h) <> each(~f,t)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  each(~(x => U32.add(U32.mul(x,3),1)),xs)
