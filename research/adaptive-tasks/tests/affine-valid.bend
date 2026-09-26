import Base
import ../slot.bend as S
import ../task.bend as T

def move_once(x: T.Run) -> T.Run:
  T.run(1n,x)
def extract_once(x: S.Slot<T.Payload>) -> S.Take<T.Payload>:
  S.take(T.Payload,x)
