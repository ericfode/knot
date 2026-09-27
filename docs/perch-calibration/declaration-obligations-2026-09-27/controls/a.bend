import Base

def step(acc: U32, item: U32) -> U32:
  U32.add(U32.mul(acc,31),item)

def fold(items: List<&2,U32>, acc: U32) -> U32:
  match items:
    case Nil{}: acc
    case Con{head,tail}: fold(tail,step(acc,head))

def Fingerprint.of(items: List<&2,U32>) -> U32:
  fold(items,0)
