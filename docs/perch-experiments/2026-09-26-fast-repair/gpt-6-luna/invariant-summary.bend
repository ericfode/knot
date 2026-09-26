import Base

def total(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case h <> t: U32.add(h, total(t))

def add_total(xs: List<&2,U32>, s: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t: U32.add(h, s) <> add_total(t, s)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  add_total(xs, total(xs))
