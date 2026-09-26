import Base

def total(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case h <> t: U32.add(h,total(t))

def annotate(xs: List<&2,U32>, +sum: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.add(h,sum) <> annotate(t,sum)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  annotate(xs,total(xs))
