type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def open(b: Box<Flag>) -> Flag:
  match b:
    case Box{v}:
      v

def peek(b: Box<Box<Flag> >) -> Flag:
  match b:
    case Box{inner}:
      open(inner)

def main() -> Flag:
  peek(Box{Box{On{}}})
