import Base
import ../main.bend as V

def illegal(v: V.Vec<U32>) -> V.Vec<U32> & V.Vec<U32>:
  (v,v)
