type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def wrap() # c
  -> Box<Flag>:
  Box{On{}}

def main() -> Flag:
  On{}
