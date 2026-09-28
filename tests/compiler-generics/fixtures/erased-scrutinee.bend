# Negative twin of box-unbox: an erased generic box is inspected by a live match.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def peek(-A: Type, -b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  peek(Flag, Box{On{}})
