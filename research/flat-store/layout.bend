import Base
import ../owned-store/store.bend as S

type Error is Data:
  CapacityLimit{}
  IndexBounds{}
  LocatorArity{}

def encode_locator(key: S.Locator) -> List<&2,U32>:
  match key:
    case S.Locator{arena,index,generation}: [arena,index,generation]

def decode_locator(words: List<&2,U32>) -> Result<Error,S.Locator>:
  match words:
    case Con{arena,Con{index,Con{generation,Nil{}}}}: Done{S.Locator{arena,index,generation}}
    case other: Fail{LocatorArity{}}

def indexed(valid: Bool, index: U32) -> Result<Error,U32>:
  match valid:
    case False{}: Fail{IndexBounds{}}
    case True{}: Done{U32.add(32,U32.mul(16,index))}

def bounded(valid: Bool, capacity: U32, +index: U32) -> Result<Error,U32>:
  match valid:
    case False{}: Fail{CapacityLimit{}}
    case True{}: indexed(U32.is_lt(index,capacity),index)

def offset(+capacity: U32, index: U32) -> Result<Error,U32>:
  bounded(U32.is_le(capacity,4096),capacity,index)
