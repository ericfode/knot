def open(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{value}: value

type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  open(Flag, Box{On{}})
