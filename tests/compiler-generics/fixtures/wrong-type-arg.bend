# Negative twin of box-unbox: the explicit type argument disagrees with the box.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  unbox(Color, Box{On{}})
