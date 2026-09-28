def peek(x: Flag) -> Flag:
  b: Box<Flag> = Box{x}
  match b:
    case Box{v}:
      v

type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  peek(On{})
