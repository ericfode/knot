type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def make() -> Box<Type>:
  Box{Flag}

def main() -> Flag:
  On{}
