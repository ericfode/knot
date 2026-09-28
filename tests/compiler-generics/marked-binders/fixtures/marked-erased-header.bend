type Flag is Data:
  Off{}
  On{}

type Box<-a, -A: Kind(a)> is Kind(a):
  Box{value: A}

def main() -> Flag:
  On{}
