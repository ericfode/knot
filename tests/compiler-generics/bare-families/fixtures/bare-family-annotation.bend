type Flag is Data:
  Off{}
  On{}

type Bit<a> is Kind(a):
  Zero{}
  One{}

def read(x: Bit<&1>) -> Flag:
  match x:
    case Zero{}:
      Off{}
    case One{}:
      On{}

def main() -> Flag:
  y : Bit = One{}
  read(y)
