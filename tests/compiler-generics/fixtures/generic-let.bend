# A local binding annotated with an applied generic type.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def hold(x: Flag) -> Flag:
  b : Box<Flag> = Box{x}
  unbox(Flag, b)

def main() -> Flag:
  hold(On{})
