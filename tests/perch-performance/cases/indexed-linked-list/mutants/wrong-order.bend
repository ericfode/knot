import Base

def walk(xs: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case h <> t:
      U32.mul(h,i) <> walk(t,U32.add(i,1))

def forward(xs: List<&2,U32>) -> List<&2,U32>:
  walk(xs,1)

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  List.reverse(&2,U32,forward(xs))
