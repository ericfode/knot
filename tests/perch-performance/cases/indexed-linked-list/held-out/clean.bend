import Base

def emit(xs: List<&2,U32>, +i: U32, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: List.reverse(&2,U32,acc)
    case h <> t: emit(t,U32.add(i,1),U32.mul(h,i) <> acc)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  emit(xs,1,Nil{})
