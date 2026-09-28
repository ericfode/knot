type Bit is Data:
  Low{}
  High{}

def apply(f: Bit -> Bit, x: Bit) -> Bit:
  f(x)

def identity(x: Bit) -> Bit:
  apply(y => y,x)
