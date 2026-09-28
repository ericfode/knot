import Base
import ./main.bend as B

# Deliberately simple ordered list model. Never calls emit or finish.
def join(a: List<&2,String>, b: List<&2,String>) -> List<&2,String>:
  match a:
    case Nil{}:
      b
    case Con{head, tail}:
      Con{head, join(tail, b)}

def flatten(parts: List<&2,String>) -> String:
  match parts:
    case Nil{}:
      SNil{}
    case Con{head, tail}:
      String.append(head, flatten(tail))

# Abstraction only; model operations above know nothing about the tree.
def chunks(builder: B.Builder) -> List<&2,String>:
  match builder:
    case B.Empty{}:
      Nil{}
    case B.Chunk{text}:
      Con{text, Nil{}}
    case B.Join{left, right}:
      join(chunks(left), chunks(right))
