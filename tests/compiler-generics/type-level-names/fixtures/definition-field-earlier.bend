type Flag is Data:
  Off{}
  On{}

def T() -> Type:
  Flag

type Box<-A: Type> is Type:
  Box{value: T}

def unb(b: Box<Flag>) -> Flag:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  unb(Box{On{}})
