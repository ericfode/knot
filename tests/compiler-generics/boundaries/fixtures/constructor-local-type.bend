type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{-B: Type, value: B}

def main() -> Flag:
  On{}
