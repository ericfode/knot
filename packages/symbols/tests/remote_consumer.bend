import Base
import 0xf5507d46d06a1a8043dcb1a582194615/main.bend as S
import 0xf5507d46d06a1a8043dcb1a582194615/release.bend as Verified

# A successful consumer returns 1 only when the exact Unicode name round-trips.
def resolved(pair: S.Table & Result<S.Error,String>) -> U32:
  (t,r) = pair
  match r:
    case Fail{e}: 0
    case Done{name}: Bool.to_u32(String.eq(name,"compiler.λ"))

def interned(pair: S.Table & Result<S.Error,U32>) -> U32:
  (t,r) = pair
  match r:
    case Fail{e}: 0
    case Done{id}: resolved(S.Table.resolve(t,id))

def main() -> U32:
  interned(S.Table.intern(S.Table.new(),"compiler.λ"))
