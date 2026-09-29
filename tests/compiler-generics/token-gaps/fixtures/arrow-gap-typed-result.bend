# The smallest generic: one erased type parameter, one instantiation.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def boxed(x: Flag) - > Box<Flag>:
  Box{x}

def round(x: Flag) -> Flag:
  unbox(Flag, Box{x})

def main() -> Flag:
  round(On{})
