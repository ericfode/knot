type Flag is Data:
  Off{}
  On{}

def id(x: Flag) -> Flag:
  x

def main() -> Flag:
  id

type Box<-A: Type> is Type:
  Box{value: A}
