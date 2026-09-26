import Base

def chunks(xs: List<&2,U32>) -> List<&2,List<&2,U32>>:
  match xs:
    case Nil{}: Nil{}
    case h <> t: [U32.add(U32.mul(h,3),1)] <> chunks(t)

def assemble(parts: List<&2,List<&2,U32>>, result: List<&2,U32>) -> List<&2,U32>:
  match parts:
    case Nil{}: result
    case h <> t: assemble(t,List.append(&2,U32,result,h))

def solve(xs: List<&2,U32>) -> List<&2,U32>:
  assemble(chunks(xs),Nil{})
