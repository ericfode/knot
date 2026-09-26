import Base
import ../../main.bend as S

def bad() -> S.Scopes & Result<S.Error,S.Store<(U32 -> U32)>>:
  S.Store.new((U32 -> U32),S.Scopes.new(),1)
