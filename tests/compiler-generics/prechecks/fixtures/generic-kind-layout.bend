type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Kind(&1) # c

  :
  Box{value: A}

def main() -> Flag:
  On{}
