type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def same(xs: +Box<Flag>) -> Flag:
  On{}

def main() -> Flag:
  On{}
