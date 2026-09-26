import Base

def walk(+xs: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Cons{head, tail}:
      U32.mul(head,U32.add(i,1u)) <> walk(tail,U32.add(i,1u))

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,0u)
