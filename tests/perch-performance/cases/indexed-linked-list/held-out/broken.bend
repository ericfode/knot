import Base

def lookup(xs: List<&2,U32>, n: Nat) -> U32:
  match xs n:
    case Nil{} _: 0
    case h <> t 0n: h
    case h <> t 1n+p: lookup(t,p)

def emit(+all: List<&2,U32>, rest: List<&2,U32>, +i: Nat) -> List<&2,U32>:
  match rest:
    case Nil{}: Nil{}
    case h <> t:
      U32.mul(lookup(all,i),U32.from_nat(1n+i)) <> emit(all,t,1n+i)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  emit(xs,xs,0n)
