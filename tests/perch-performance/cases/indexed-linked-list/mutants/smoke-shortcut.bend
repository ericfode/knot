import Base

def walk(xs: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.mul(h,i) <> walk(t,U32.add(i,1))

def forward(xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,1)

def choose(xs: List<&2,U32>, too_long: Bool) -> List<&2,U32>:
  match too_long:
    case True{}: Nil{}
    case False{}: forward(xs)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  choose(xs,U32.is_gt(U32.from_nat(List.length(&2,U32,xs)),32))
