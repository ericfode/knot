def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  unbox(Flag, Box{On{}})

type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}
