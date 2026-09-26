import Base

def head_or_zero(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case h <> t: h

def walk(+all: List<&2,U32>, remaining: List<&2,U32>, +index: Nat) -> List<&2,U32>:
  match remaining:
    case Nil{}: Nil{}
    case h <> t:
      U32.mul(head_or_zero(List.drop(&2,U32,all,index)),U32.from_nat(1n+index)) <> walk(all,t,1n+index)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,xs,0n)
