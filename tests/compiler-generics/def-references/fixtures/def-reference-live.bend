type Flag is Data:
  Off{}
  On{}

def one() -> Flag:
  On{}

def main() -> Flag:
  one

type Box<-A: Type> is Type:
  Box{value: A}
