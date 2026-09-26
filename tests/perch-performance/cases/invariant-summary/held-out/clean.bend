import Base

def sum_into(xs: List<&2,U32>, acc: U32) -> U32:
  match xs:
    case Nil{}: acc
    case h <> t: sum_into(t,U32.add(acc,h))

def build(xs: List<&2,U32>, +sum: U32, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: List.reverse(&2,U32,acc)
    case h <> t: build(t,sum,U32.add(h,sum) <> acc)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  build(xs,sum_into(xs,0),Nil{})
