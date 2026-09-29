# The smallest generic: one erased type parameter, one instantiation.
type Flag is Data:
  Off{}
  On{}

type Shade is Data:
  Dim {}
  Lit {}

type Box<-A: Type> is Type:
  Box {value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def round(x: Flag) -> Flag:
  unbox(Flag, Box{x})

def main() -> Flag:
  round(On{})
