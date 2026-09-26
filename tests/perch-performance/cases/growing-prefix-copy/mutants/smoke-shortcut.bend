import Base

def collect(xs: List<&2,U32>, acc: List<&2,U32>) -> List<&2,U32>:
  match xs:
    case Nil{}: List.reverse(&2,U32,acc)
    case h <> t:
      collect(t,U32.add(U32.mul(h,3),1) <> acc)

def forward(xs: List<&2,U32>) -> List<&2,U32>:
  collect(xs,Nil{})

def choose(xs: List<&2,U32>, too_long: Bool) -> List<&2,U32>:
  match too_long:
    case True{}: Nil{}
    case False{}: forward(xs)

def solve(+xs: List<&2,U32>) -> List<&2,U32>:
  choose(xs,U32.is_gt(U32.from_nat(List.length(&2,U32,xs)),32))
