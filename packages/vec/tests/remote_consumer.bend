import Base
import 0xd684886d10b431b9dce6c3b2d1ef1980/release.bend as Release
import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V

def read(pair: V.Vec<U32> & Result<V.Error,U32>) -> Bool:
  (v,r) = pair
  match r:
    case Fail{e}: False{}
    case Done{x}: U32.is_eq(x,42)

def pushed(pair: V.Vec<U32> & Result<V.Error,Unit>) -> Bool:
  (v,r) = pair
  read(V.Vec.get(U32,v,0))

def main() -> Bool:
  Bool.and(Release.main(),pushed(V.Vec.push(U32,V.Vec.new(U32),42)))
