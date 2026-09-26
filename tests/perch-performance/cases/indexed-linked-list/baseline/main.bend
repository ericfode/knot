import Base

def value(x: Maybe<&2,U32>) -> U32:
  match x:
    case None{}: 0
    case Some{v}: v

def walk(+xs: List<&2,U32>, n: Nat, +i: Nat) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+p:
      U32.mul(value(List.get(&2,U32,xs,i)),U32.from_nat(1n+i)) <> walk(xs,p,1n+i)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,List.length(&2,U32,xs),0n)
