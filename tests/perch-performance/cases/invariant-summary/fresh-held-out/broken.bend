import Base

def sum(xs: List<&2,U32>) -> U32:
  List.foldl(~&2,~U32,~U32,~U32.add,xs,0)

def visit(+all: List<&2,U32>, remaining: List<&2,U32>) -> List<&2,U32>:
  match remaining:
    case Nil{}: Nil{}
    case h <> t: U32.add(h,sum(all)) <> visit(all,t)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  visit(xs,xs)
