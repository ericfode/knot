# A type-returning definition used as a parameter type: Wrap(Flag) is Box<Flag>.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def Wrap(A: Type) -> Type:
  Box<A>

def open(b: Wrap(Flag)) -> Flag:
  match b:
    case Box{v}:
      v

def run(x: Flag) -> Flag:
  open(Box{x})

def main() -> Flag:
  run(On{})
