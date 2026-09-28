type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: Missing}

def main() -> Flag:
  On{}
