type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def open(b: Box<Flag>) -> Flag:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  b: Box<Flag > = Box{On{}}
  open(b)
