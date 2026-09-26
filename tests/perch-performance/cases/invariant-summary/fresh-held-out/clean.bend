import Base

def sum(xs: List<&2,U32>) -> U32:
  List.foldl(~&2,~U32,~U32,~U32.add,xs,0)

def visit(+amount: U32, remaining: List<&2,U32>) -> List<&2,U32>:
  match remaining:
    case Nil{}: Nil{}
    case h <> t: U32.add(h,amount) <> visit(amount,t)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  visit(sum(xs),xs)
