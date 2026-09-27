import Base
import ./bytes.bend as B

def join(a: List<&2,List<&2,U32>>, b: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match a:
    case Nil{}:
      b
    case Con{h,t}:
      Con{h,join(t,b)}

def flatten(parts: List<&2,List<&2,U32>>) -> List<&2,U32>:
  match parts:
    case Nil{}:
      Nil{}
    case Con{h,t}:
      List.append(&2,U32,h,flatten(t))

def chunks(tree: B.Tree) -> List<&2,List<&2,U32>>:
  match tree:
    case B.Empty{}:
      Nil{}
    case B.Chunk{values}:
      Con{values,Nil{}}
    case B.Join{a,b}:
      join(chunks(a),chunks(b))

# Observation adapter, not an oracle: strips private tree grouping.
def observe(result: Result<B.Error,B.Builder>) -> Result<B.Error,List<&2,U32> & U32>:
  match result:
    case Fail{err}:
      Fail{err}
    case Done{+b}:
      Done{(B.finish(b),B.length(b))}
