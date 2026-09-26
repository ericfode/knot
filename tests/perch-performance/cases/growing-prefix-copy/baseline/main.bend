import Base

def collect(xs: List<&2,U32>, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: acc
    case h <> t:
      collect(t,List.append(&2,U32,acc,[U32.add(U32.mul(h,3),1)]))

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  collect(xs,Nil{})
