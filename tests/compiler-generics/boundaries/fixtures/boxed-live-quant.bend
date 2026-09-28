type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def make() -> Box<Quant>:
  Box{&2}

def main() -> Flag:
  On{}
