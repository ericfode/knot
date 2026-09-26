import Base

def collect(xs: List<&2,U32>, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: List.reverse(&2,U32,acc)
    case h <> t: collect(t,U32.add(U32.mul(h,3),1) <> acc)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  collect(xs,Nil{})
