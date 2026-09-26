import Base
import ../../main.bend as S

def bad(m: S.Memo<U32,U32>) -> S.Memo<U32,U32> & S.Memo<U32,U32>:
  (m,m)
