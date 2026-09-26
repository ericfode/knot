import Base
import ./main.bend as V

def finish(pair: V.Vec<U32> & Result<V.Error,U32>) -> U32:
  (v,r) = pair
  match r:
    case Fail{e}:
      0
    case Done{x}:
      x

def pushed(pair: V.Vec<U32> & Result<V.Error,Unit>) -> U32:
  (v,r) = pair
  finish(V.Vec.get(U32,v,0))

def main() -> U32:
  pushed(V.Vec.push(U32,V.Vec.new(U32),42))
