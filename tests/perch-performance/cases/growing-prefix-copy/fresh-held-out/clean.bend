import Base

def chunks(xs: List<&2,U32>) -> List<&2,List<&2,U32>>:
  match xs:
    case Nil{}: Nil{}
    case h <> t: [U32.add(U32.mul(h,3),1)] <> chunks(t)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  List.concat(&2,U32,chunks(xs))
