import Base

def append_one(xs: List<&2,U32>, x: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: [x]
    case h <> t: h <> append_one(t,x)

def build(xs: List<&2,U32>, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: acc
    case h <> t: build(t,append_one(acc,U32.add(U32.mul(h,3),1)))

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  build(xs,Nil{})
