type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: Box<T>}

def T() -> Type:
  Flag

def main() -> Flag:
  On{}
