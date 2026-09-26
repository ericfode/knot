import Base

def head_or_zero(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case h <> t: h

def walk(xs: List<&2,U32>, +index: Nat) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.mul(h,U32.from_nat(1n+index)) <> walk(t,1n+index)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,0n)
