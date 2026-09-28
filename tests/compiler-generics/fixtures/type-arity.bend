# A one-parameter family applied to two type arguments.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def open(b: Box<Flag, Flag>) -> Flag:
  unbox(Flag, b)

def main() -> Flag:
  On{}
