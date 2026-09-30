type Flag is Data # c
  :
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  On{}
