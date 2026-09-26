import Base
import ../slot.bend as S
import ../task.bend as T

def take_twice(x: S.Slot<T.Payload>) -> S.Take<T.Payload> & S.Take<T.Payload>:
  (S.take(T.Payload,x),S.take(T.Payload,x))
