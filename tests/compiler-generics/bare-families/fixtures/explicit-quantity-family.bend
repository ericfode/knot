type Flag is Data:
  Off{}
  On{}

type Bit<a> is Kind(a):
  Zero{}
  One{}

def mk(x: Flag) -> Bit<&1>:
  match x:
    case Off{}:
      Zero{}
    case On{}:
      One{}

def read(x: Bit<&1>) -> Flag:
  match x:
    case Zero{}:
      Off{}
    case One{}:
      On{}

def pick(x: Flag) -> Flag:
  read(mk(x))

def main() -> Flag:
  pick(On{})
