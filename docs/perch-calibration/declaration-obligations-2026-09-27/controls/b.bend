import Base

def relay(flag: Bool, value: U32) -> U32:
  match flag:
    case True{}: U32.add(value,0)
    case False{}: U32.mul(value,1)

def step(+acc: U32, +item: U32) -> U32:
  relay(U32.is_eq(acc,item),
    relay(U32.is_eq(item,acc),
      U32.add(U32.mul(relay(True{},acc),31),relay(False{},item))))

def fold(items: List<&2,U32>, acc: U32) -> U32:
  match items:
    case Nil{}: acc
    case Con{head,tail}: fold(tail,step(acc,head))

def Fingerprint.of(items: List<&2,U32>) -> U32:
  fold(items,0)
