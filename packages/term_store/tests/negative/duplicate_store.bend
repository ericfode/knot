import Base
import ../../main.bend as S

def bad(s: S.Store<U32>) -> S.Store<U32> & S.Store<U32>:
  (s,s)
