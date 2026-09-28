type Flag is Data:
  Off{}
  On{}

type Void is Type:

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  On{}
