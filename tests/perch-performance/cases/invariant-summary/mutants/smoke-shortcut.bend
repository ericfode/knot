import Base

def total(xs: List<&2,U32>) -> U32:
  match xs:
    case Nil{}: 0
    case h <> t: U32.add(h,total(t))

def annotate(xs: List<&2,U32>, +sum: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.add(h,sum) <> annotate(t,sum)

def forward(+xs: List<&2,U32>) -> List<&2,U32>:
  annotate(xs,total(xs))

def choose(xs: List<&2,U32>, too_long: Bool) -> List<&2,U32>:
  match too_long:
    case True{}: Nil{}
    case False{}: forward(xs)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  choose(xs,U32.is_gt(U32.from_nat(List.length(&2,U32,xs)),32))
