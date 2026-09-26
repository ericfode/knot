import Base

def walk(xs: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case x <> tail:
      U32.mul(x,i) <> walk(tail,U32.add(i,1))

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,1)
