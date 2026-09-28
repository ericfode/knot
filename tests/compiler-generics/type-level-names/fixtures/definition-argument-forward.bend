type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def f(b: Box<T>) -> Flag:
  On{}

def T() -> Type:
  Flag

def main() -> Flag:
  On{}
